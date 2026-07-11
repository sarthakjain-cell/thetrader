import sqlite3
import pandas as pd
import numpy as np
from itertools import product
from datetime import timedelta
from strategy_v3 import StrategyV3
from logger import log

DB_PATH = "trading_system.db"

PARAM_GRID = {
    'fast_ema': [5, 8, 10, 13],
    'slow_ema': [30, 40, 50],
    'rsi_thresh': [50, 55, 60],
    'adx_thresh': [15, 18, 20]
}

def load_multi_asset_data():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM market_data_1d ORDER BY Datetime ASC", conn)
    conn.close()
    df['Datetime'] = pd.to_datetime(df['Datetime'])
    return df

def get_data_splits(df_all):
    max_date = df_all['Datetime'].max()
    test_start = max_date - timedelta(days=365)
    val_start = test_start - timedelta(days=365)
    return val_start, test_start

def evaluate_portfolio_on_window(df_dict, params, start_date, end_date):
    results = []
    portfolio_equity = None
    
    for sym, sym_df in df_dict.items():
        if len(sym_df) < 100: continue
        
        # Pre-warm indicators on full data
        strat = StrategyV3(sym_df, params)
        
        # Slice to window
        mask = (strat.df['Datetime'] >= start_date) & (strat.df['Datetime'] < end_date)
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

def run_multi_asset_optimizer():
    df_all = load_multi_asset_data()
    symbols = df_all['Symbol'].unique()
    val_start, test_start = get_data_splits(df_all)
    
    df_dict = {sym: df_all[df_all['Symbol'] == sym].copy() for sym in symbols}
    
    keys, values = zip(*PARAM_GRID.items())
    combinations = [dict(zip(keys, v)) for v in product(*values)]
    
    log.info(f"Iteration 3 Grid Search: {len(combinations)} combinations.")
    log.info(f"Val Window:   {val_start.date()} -> {test_start.date()}")
    log.info(f"Test Window:  {test_start.date()} -> End")
    
    best_pf = -1.0
    best_params = None
    best_mdd = 1.0
    best_trades = 0
    
    # Optimize on VALIDATION set
    for i, p in enumerate(combinations):
        pf, mdd, trades = evaluate_portfolio_on_window(df_dict, p, val_start, test_start)
        
        if pf > best_pf:
            best_pf = pf
            best_params = p
            best_mdd = mdd
            best_trades = trades
                
        if (i + 1) % 25 == 0:
            log.info(f"Val Tested {i+1}/{len(combinations)}...")
            
    log.info("--- DIAGNOSTIC RAW OPTIMIZATION COMPLETE ---")
    if best_params:
        log.info(f"🥇 RAW BEST VAL PARAMS: {best_params}")
        log.info(f"📈 RAW VAL Portfolio PF: {best_pf:.2f} | MDD: {best_mdd*100:.2f}%")
        log.info(f"📊 RAW VAL Total Trades: {best_trades} | Avg per stock: {best_trades/13:.1f}")
        log.info(f"Gate Check: Would it have passed MDD < 10%? {'YES' if best_mdd < 0.10 else 'NO'}")
        log.info(f"Gate Check: Would it have passed 60 trades? {'YES' if best_trades >= 60 else 'NO'}")

if __name__ == "__main__":
    run_multi_asset_optimizer()
