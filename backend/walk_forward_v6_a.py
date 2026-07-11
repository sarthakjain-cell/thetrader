import sqlite3
import pandas as pd
import numpy as np
from itertools import product
from datetime import timedelta
from strategy_v6_a import StrategyV6A
from logger import log

DB_PATH = "trading_system.db"

PARAM_GRID = {
    'rsi_thresh_a': [35, 40, 45],
    'atr_target_a': [1.5, 2.0, 2.5],
    'atr_stop_a': [1.0, 1.5, 2.0]
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
    nifty_df['Market_Regime_Up'] = nifty_df['Market_Regime_Up'].fillna(False)
    
    nifty_regime = nifty_df[['Datetime', 'Market_Regime_Up']]
    df_all = pd.merge(df_all, nifty_regime, on='Datetime', how='left')
    df_all['Market_Regime_Up'] = df_all['Market_Regime_Up'].fillna(False)
    
    return df_all

def apply_universe_rotation_a(df_all):
    df_all['Mom_50'] = df_all.groupby('Symbol')['Close'].pct_change(periods=50)
    df_all['YearMonth'] = df_all['Datetime'].dt.to_period('M')
    
    monthly_last_days = df_all.groupby(['Symbol', 'YearMonth'])['Datetime'].max().reset_index()
    monthly_last_days = pd.merge(monthly_last_days, df_all[['Symbol', 'Datetime', 'Mom_50']], on=['Symbol', 'Datetime'])
    
    monthly_last_days['TargetMonth'] = monthly_last_days['YearMonth'] + 1
    monthly_last_days['Rank'] = monthly_last_days.groupby('TargetMonth')['Mom_50'].rank(ascending=False, method='first')
    monthly_last_days['Is_Top_5'] = (monthly_last_days['Rank'] <= 5) & (monthly_last_days['Mom_50'] > 0)
    
    mapping = monthly_last_days[['Symbol', 'TargetMonth', 'Is_Top_5']].rename(columns={'TargetMonth': 'YearMonth'})
    df_all = pd.merge(df_all, mapping, on=['Symbol', 'YearMonth'], how='left')
    df_all['Entry_Allowed'] = df_all['Is_Top_5'].fillna(False)
    
    return df_all

def get_data_splits(df_all):
    max_date = df_all['Datetime'].max()
    test_start = max_date - timedelta(days=365)
    val_start = test_start - timedelta(days=365)
    return val_start, test_start

def evaluate_portfolio_on_window(df_dict, params, start_date, end_date):
    results = []
    portfolio_equity = None
    
    # 50-day warm-up skip explicitly added
    warmup_period = timedelta(days=50)
    
    for sym, sym_df in df_dict.items():
        if len(sym_df) < 100: continue
        
        strat = StrategyV6A(sym_df, params)
        
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

def run_optimizer_a():
    df_all = load_multi_asset_data()
    log.info("Applying Market Regime Filter...")
    df_all = apply_market_regime(df_all)
    
    log.info("Applying Mode A Rotation (Top 5 Mom)...")
    df_all = apply_universe_rotation_a(df_all)
    
    symbols = df_all['Symbol'].unique()
    val_start, test_start = get_data_splits(df_all)
    
    df_dict = {sym: df_all[df_all['Symbol'] == sym].copy() for sym in symbols}
    
    keys, values = zip(*PARAM_GRID.items())
    combinations = [dict(zip(keys, v)) for v in product(*values)]
    
    log.info(f"Iteration 6 Mode A Grid Search: {len(combinations)} combinations.")
    
    best_pf = 0
    best_params = None
    best_mdd = 1.0
    best_trades = 0
    
    for i, p in enumerate(combinations):
        pf, mdd, trades = evaluate_portfolio_on_window(df_dict, p, val_start, test_start)
        
        # No trade gate to see pure performance first, but we prioritize PF
        if mdd < 0.10:
            if pf > best_pf:
                best_pf = pf
                best_params = p
                best_mdd = mdd
                best_trades = trades
                
        if (i + 1) % 10 == 0:
            log.info(f"Mode A Val Tested {i+1}/{len(combinations)}...")
            
    log.info("--- MODE A OPTIMIZATION COMPLETE ---")
    if best_params:
        log.info(f"🥇 BEST VAL PARAMS A: {best_params}")
        log.info(f"📈 VAL Portfolio PF A: {best_pf:.2f} | MDD: {best_mdd*100:.2f}% | Trades: {best_trades}")
    else:
        log.warning("❌ No parameter set met MDD < 10% for Mode A.")

if __name__ == "__main__":
    run_optimizer_a()
