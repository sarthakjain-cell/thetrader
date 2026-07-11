import sqlite3
import pandas as pd
import numpy as np
from itertools import product
from strategy_v7_orb import StrategyV7ORB
from strategy_v7_vwap import StrategyV7VWAP
from logger import log

DB_PATH = "trading_system.db"

PARAM_GRID_ORB = {
    'orb_bars': [3, 6],          # 15m or 30m
    'orb_target': [1.0, 1.5, 2.0],
    'orb_stop': [0.5, 1.0]
}

PARAM_GRID_VWAP = {
    'vwap_dev_atr': [0.5, 1.0, 1.5],
    'vwap_rsi': [30, 40],
    'vwap_stop': [0.5, 1.0]
}

def load_data():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM market_data_5m ORDER BY Datetime ASC", conn)
    conn.close()
    df['Datetime'] = pd.to_datetime(df['Datetime'])
    df['Date'] = df['Datetime'].dt.date
    return df

def compute_regimes(df_all):
    log.info("Computing Intraday Regimes (ORB vs VWAP)...")
    daily_stats = df_all.groupby(['Symbol', 'Date']).agg(
        Open_Day=('Open', 'first'),
        High_Day=('High', 'max'),
        Low_Day=('Low', 'min'),
        Close_Day=('Close', 'last')
    ).reset_index()
    
    daily_stats['Prev_High'] = daily_stats.groupby('Symbol')['High_Day'].shift(1)
    daily_stats['Prev_Low'] = daily_stats.groupby('Symbol')['Low_Day'].shift(1)
    
    def get_first_bar(g):
        if len(g) > 0:
            first = g.iloc[0]
            return pd.Series({'First_Open': first['Open'], 'First_Close': first['Close'], 'First_Range': first['High'] - first['Low']})
        return pd.Series({'First_Open': np.nan, 'First_Close': np.nan, 'First_Range': np.nan})
        
    first_bars = df_all.groupby(['Symbol', 'Date']).apply(get_first_bar).reset_index()
    daily_stats = pd.merge(daily_stats, first_bars, on=['Symbol', 'Date'])
    
    daily_stats['Avg_Opening_Range_10d'] = daily_stats.groupby('Symbol')['First_Range'].transform(lambda x: x.shift(1).rolling(10).mean())
    
    # Regime Switch Logic
    def assign_regime(row):
        if pd.isna(row['Avg_Opening_Range_10d']): return 'VWAP'
        
        # Gap up/down
        is_gap = row['Open_Day'] > row['Prev_High'] or row['Open_Day'] < row['Prev_Low']
        
        if is_gap:
            # Check if reversal against gap
            gap_up = row['Open_Day'] > row['Prev_High']
            first_bar_red = row['First_Close'] < row['First_Open']
            
            gap_down = row['Open_Day'] < row['Prev_Low']
            first_bar_green = row['First_Close'] > row['First_Open']
            
            is_reversal = (gap_up and first_bar_red) or (gap_down and first_bar_green)
            
            if is_reversal:
                return 'VWAP'
                
            if row['First_Range'] > row['Avg_Opening_Range_10d']:
                return 'ORB'
                
        return 'VWAP'
        
    daily_stats['Regime'] = daily_stats.apply(assign_regime, axis=1)
    
    regime_map = daily_stats[['Symbol', 'Date', 'Regime']]
    df_all = pd.merge(df_all, regime_map, on=['Symbol', 'Date'], how='left')
    
    return df_all

def evaluate_orb_grid(df_all, dates_train):
    df_train = df_all[df_all['Date'].isin(dates_train) & (df_all['Regime'] == 'ORB')]
    symbols = df_train['Symbol'].unique()
    
    df_dict = {sym: df_train[df_train['Symbol'] == sym].copy() for sym in symbols}
    keys, values = zip(*PARAM_GRID_ORB.items())
    combinations = [dict(zip(keys, v)) for v in product(*values)]
    
    best_pf = 0
    best_params = None
    best_mdd = 1.0
    best_trades = 0
    
    log.info(f"Running ORB Optimizer ({len(combinations)} combinations) on {len(dates_train)} train days...")
    
    for i, p in enumerate(combinations):
        results = []
        portfolio_equity = None
        
        for sym, sym_df in df_dict.items():
            if len(sym_df) < 20: continue
            strat = StrategyV7ORB(sym_df, p)
            res = strat.backtest()
            
            eq_series = pd.Series(res.get('equity', [100000.0] * len(strat.df)))
            if portfolio_equity is None:
                portfolio_equity = eq_series
            else:
                min_len = min(len(portfolio_equity), len(eq_series))
                portfolio_equity = portfolio_equity.iloc[:min_len] + eq_series.iloc[:min_len] - 100000.0
                
            results.append(res)
            
        if not results: continue
        avg_pf = np.mean([r['pf'] for r in results])
        total_trades = sum(r['trades'] for r in results)
        
        rolling_max = portfolio_equity.cummax()
        drawdowns = (portfolio_equity - rolling_max) / rolling_max
        mdd = abs(drawdowns.min()) if not drawdowns.empty else 1.0
        
        if mdd < 0.10:
            if avg_pf > best_pf:
                best_pf = avg_pf
                best_params = p
                best_mdd = mdd
                best_trades = total_trades
                
    log.info(f"🥇 BEST ORB PARAMS: {best_params} | PF: {best_pf:.2f} | MDD: {best_mdd*100:.2f}% | Trades: {best_trades}")
    return best_params

def evaluate_vwap_grid(df_all, dates_train):
    df_train = df_all[df_all['Date'].isin(dates_train) & (df_all['Regime'] == 'VWAP')]
    symbols = df_train['Symbol'].unique()
    
    df_dict = {sym: df_train[df_train['Symbol'] == sym].copy() for sym in symbols}
    keys, values = zip(*PARAM_GRID_VWAP.items())
    combinations = [dict(zip(keys, v)) for v in product(*values)]
    
    best_pf = 0
    best_params = None
    best_mdd = 1.0
    best_trades = 0
    
    log.info(f"Running VWAP Optimizer ({len(combinations)} combinations) on {len(dates_train)} train days...")
    
    for i, p in enumerate(combinations):
        results = []
        portfolio_equity = None
        
        for sym, sym_df in df_dict.items():
            if len(sym_df) < 20: continue
            strat = StrategyV7VWAP(sym_df, p)
            res = strat.backtest()
            
            eq_series = pd.Series(res.get('equity', [100000.0] * len(strat.df)))
            if portfolio_equity is None:
                portfolio_equity = eq_series
            else:
                min_len = min(len(portfolio_equity), len(eq_series))
                portfolio_equity = portfolio_equity.iloc[:min_len] + eq_series.iloc[:min_len] - 100000.0
                
            results.append(res)
            
        if not results: continue
        avg_pf = np.mean([r['pf'] for r in results])
        total_trades = sum(r['trades'] for r in results)
        
        rolling_max = portfolio_equity.cummax()
        drawdowns = (portfolio_equity - rolling_max) / rolling_max
        mdd = abs(drawdowns.min()) if not drawdowns.empty else 1.0
        
        if mdd < 0.10:
            if avg_pf > best_pf:
                best_pf = avg_pf
                best_params = p
                best_mdd = mdd
                best_trades = total_trades
                
    log.info(f"🥇 BEST VWAP PARAMS: {best_params} | PF: {best_pf:.2f} | MDD: {best_mdd*100:.2f}% | Trades: {best_trades}")
    return best_params

def run_v7_optimization():
    df_all = load_data()
    # Filter out NIFTY index itself if present, as we only trade stocks
    df_all = df_all[df_all['Symbol'] != '^NSEI'].copy()
    
    df_all = compute_regimes(df_all)
    
    unique_dates = sorted(df_all['Date'].unique())
    log.info(f"Total Unique Trading Days: {len(unique_dates)}")
    
    # Static split: 1-40 Train, 41-50 Val, 51-60 Test
    if len(unique_dates) < 50:
        log.warning("Not enough data to form Train/Val splits! We have <50 days.")
        return
        
    dates_train = unique_dates[:40]
    dates_val = unique_dates[40:50]
    dates_test = unique_dates[50:60] if len(unique_dates) >= 60 else unique_dates[50:]
    
    log.info(f"Train Window: {dates_train[0]} to {dates_train[-1]}")
    
    best_orb = evaluate_orb_grid(df_all, dates_train)
    best_vwap = evaluate_vwap_grid(df_all, dates_train)
    
    # We will output these params to be hardcoded into final_exam_v7.py
    
if __name__ == "__main__":
    run_v7_optimization()
