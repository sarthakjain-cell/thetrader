import sqlite3
import pandas as pd
import numpy as np
from itertools import product
from datetime import timedelta
from strategy_v6_b import StrategyV6B
from logger import log

DB_PATH = "trading_system.db"

PARAM_GRID = {
    'rsi_thresh_b': [25, 30, 35],
    'vol_mult_b': [1.0, 1.2, 1.5],
    'atr_target_b': [1.0, 1.5, 2.0],
    'max_holding_days_b': [2, 3, 5]
}

def load_multi_asset_data():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM market_data_1d ORDER BY Datetime ASC", conn)
    conn.close()
    df['Datetime'] = pd.to_datetime(df['Datetime'])
    return df

def apply_market_regime(df_all):
    conn = sqlite3.connect(DB_PATH)
    nifty_df = pd.read_sql("SELECT Datetime, Close as Nifty_Close FROM nifty_index ORDER BY Datetime ASC", conn)
    conn.close()
    
    nifty_df['Datetime'] = pd.to_datetime(nifty_df['Datetime'])
    nifty_df['Nifty_SMA_200'] = nifty_df['Nifty_Close'].rolling(window=200).mean()
    nifty_df['Market_Regime_Up'] = nifty_df['Nifty_Close'] > nifty_df['Nifty_SMA_200']
    nifty_df['Market_Regime_Up'] = nifty_df['Market_Regime_Up'].fillna(True) # Fill true default
    
    nifty_regime = nifty_df[['Datetime', 'Market_Regime_Up']]
    df_all = pd.merge(df_all, nifty_regime, on='Datetime', how='left')
    df_all['Market_Regime_Up'] = df_all['Market_Regime_Up'].fillna(True)
    
    return df_all

def apply_universe_rotation_b(df_all):
    # 1. Calculate 14-day RSI for ranking
    def calculate_rsi(series, window=14):
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
        
    df_all['RSI_14'] = df_all.groupby('Symbol')['Close'].transform(lambda x: calculate_rsi(x))
    
    # 2. Calculate Distance from 50-EMA
    def calculate_ema(series, window=50):
        return series.ewm(span=window, adjust=False).mean()
        
    df_all['EMA_50'] = df_all.groupby('Symbol')['Close'].transform(lambda x: calculate_ema(x))
    df_all['EMA_Dist'] = (df_all['Close'] / df_all['EMA_50']) * 100
    
    df_all['YearMonth'] = df_all['Datetime'].dt.to_period('M')
    
    # We rank on the last day of each month
    monthly_last_days = df_all.groupby(['Symbol', 'YearMonth'])['Datetime'].max().reset_index()
    monthly_last_days = pd.merge(monthly_last_days, df_all[['Symbol', 'Datetime', 'RSI_14', 'EMA_Dist']], on=['Symbol', 'Datetime'])
    
    monthly_last_days['TargetMonth'] = monthly_last_days['YearMonth'] + 1
    
    # rank_RSI: lowest RSI gets rank 1
    monthly_last_days['Rank_RSI'] = monthly_last_days.groupby('TargetMonth')['RSI_14'].rank(ascending=True, method='first')
    
    # rank_EMA_dist: lowest % (farthest below) gets rank 1
    monthly_last_days['Rank_EMA_Dist'] = monthly_last_days.groupby('TargetMonth')['EMA_Dist'].rank(ascending=True, method='first')
    
    # Composite Score
    monthly_last_days['Composite_Score'] = monthly_last_days['Rank_RSI'] + monthly_last_days['Rank_EMA_Dist']
    
    # Rank Composite Score: lowest combined rank gets rank 1
    monthly_last_days['Final_Rank'] = monthly_last_days.groupby('TargetMonth')['Composite_Score'].rank(ascending=True, method='first')
    
    monthly_last_days['Is_Top_5_Oversold'] = monthly_last_days['Final_Rank'] <= 5
    
    mapping = monthly_last_days[['Symbol', 'TargetMonth', 'Is_Top_5_Oversold']].rename(columns={'TargetMonth': 'YearMonth'})
    df_all = pd.merge(df_all, mapping, on=['Symbol', 'YearMonth'], how='left')
    df_all['Entry_Allowed_B'] = df_all['Is_Top_5_Oversold'].fillna(False)
    
    return df_all

def get_data_splits(df_all):
    max_date = df_all['Datetime'].max()
    test_start = max_date - timedelta(days=365)
    val_start = test_start - timedelta(days=365)
    return val_start, test_start

def evaluate_portfolio_on_window(df_dict, params, start_date, end_date):
    results = []
    portfolio_equity = None
    
    warmup_period = timedelta(days=50)
    
    for sym, sym_df in df_dict.items():
        if len(sym_df) < 100: continue
        
        strat = StrategyV6B(sym_df, params)
        
        mask = (strat.df['Datetime'] >= (start_date + warmup_period)) & (strat.df['Datetime'] < end_date)
        strat.df = strat.df[mask].copy()
        
        if len(strat.df) < 50: continue
        
        res = strat.backtest()
        
        eq_series = pd.Series(res.get('equity', [100000.0] * len(strat.df)))
        if portfolio_equity is None:
            portfolio_equity = eq_series
        else:
            min_len = min(len(portfolio_equity), len(eq_series))
            portfolio_equity = portfolio_equity.iloc[:min_len] + eq_series.iloc[:min_len] - 100000.0
            
        results.append(res)
        
    if not results:
        return 0, 1.0, 0
        
    avg_pf = np.mean([r['pf'] for r in results])
    total_trades = sum(r['trades'] for r in results)
    
    rolling_max = portfolio_equity.cummax()
    drawdowns = (portfolio_equity - rolling_max) / rolling_max
    portfolio_mdd = abs(drawdowns.min()) if not drawdowns.empty else 1.0
    
    return avg_pf, portfolio_mdd, total_trades

def run_optimizer_b():
    df_all = load_multi_asset_data()
    log.info("Applying Market Regime Filter...")
    df_all = apply_market_regime(df_all)
    
    log.info("Applying Mode B Rotation (Top 5 Composite Oversold)...")
    df_all = apply_universe_rotation_b(df_all)
    
    symbols = df_all['Symbol'].unique()
    val_start, test_start = get_data_splits(df_all)
    
    df_dict = {sym: df_all[df_all['Symbol'] == sym].copy() for sym in symbols}
    
    keys, values = zip(*PARAM_GRID.items())
    combinations = [dict(zip(keys, v)) for v in product(*values)]
    
    log.info(f"Iteration 6 Mode B Grid Search: {len(combinations)} combinations.")
    
    best_pf = 0
    best_params = None
    best_mdd = 1.0
    best_trades = 0
    
    for i, p in enumerate(combinations):
        pf, mdd, trades = evaluate_portfolio_on_window(df_dict, p, val_start, test_start)
        
        if mdd < 0.10:
            if pf > best_pf:
                best_pf = pf
                best_params = p
                best_mdd = mdd
                best_trades = trades
                
        if (i + 1) % 25 == 0:
            log.info(f"Mode B Val Tested {i+1}/{len(combinations)}...")
            
    log.info("--- MODE B OPTIMIZATION COMPLETE ---")
    if best_params:
        log.info(f"🥇 BEST VAL PARAMS B: {best_params}")
        log.info(f"📈 VAL Portfolio PF B: {best_pf:.2f} | MDD: {best_mdd*100:.2f}% | Trades: {best_trades}")
    else:
        log.warning("❌ No parameter set met MDD < 10% for Mode B.")

if __name__ == "__main__":
    run_optimizer_b()
