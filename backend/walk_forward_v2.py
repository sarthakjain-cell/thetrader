import sqlite3
import pandas as pd
import numpy as np
from itertools import product
from strategy_v2 import StrategyV2
from logger import log

DB_PATH = "trading_system.db"

# The Grid Search Parameter Space (Trailing stops removed, ATR fixed to 2.5/3.0)
PARAM_GRID = {
    'fast_ema': [5, 9],
    'slow_ema': [21, 50],
    'rsi_thresh': [55, 60],
    'adx_thresh': [20, 25],
    'stop_atr_mult': [2.5, 3.0]
}

def load_multi_asset_data():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM market_data_1d ORDER BY Datetime ASC", conn)
    conn.close()
    df['Datetime'] = pd.to_datetime(df['Datetime'])
    return df

def evaluate_portfolio(df_dict, params):
    """Runs the strategy on all stocks and returns portfolio average metrics."""
    results = []
    
    for sym, sym_df in df_dict.items():
        if len(sym_df) < 50: 
            continue
            
        strat = StrategyV2(sym_df, params)
        res = strat.backtest(initial_capital=100000.0, risk_per_trade=0.01)
        results.append(res)
        
    if not results:
        return 0, 1.0, 0
        
    avg_pf = np.mean([r['pf'] for r in results])
    avg_mdd = np.mean([r['mdd'] for r in results])
    total_trades = sum(r['trades'] for r in results)
    
    return avg_pf, avg_mdd, total_trades

def run_multi_asset_optimizer():
    df_all = load_multi_asset_data()
    symbols = df_all['Symbol'].unique()
    
    log.info(f"Loaded {len(df_all)} rows across {len(symbols)} NIFTY 50 assets.")
    
    df_dict = {sym: df_all[df_all['Symbol'] == sym].copy() for sym in symbols}
    
    keys, values = zip(*PARAM_GRID.items())
    combinations = [dict(zip(keys, v)) for v in product(*values)]
    
    log.info(f"Initiating Grid Search: {len(combinations)} parameter combinations.")
    log.info(f"Objective: Maximize Average Profit Factor with Portfolio MDD < 10%.")
    
    best_pf = 0
    best_params = None
    best_mdd = 1.0
    valid_configs = 0
    
    for i, p in enumerate(combinations):
        pf, mdd, trades = evaluate_portfolio(df_dict, p)
        
        # Acceptance Criteria: Strict Drawdown Control (< 10%) & Minimum Trades (> 20)
        if mdd < 0.10 and trades > 20:
            valid_configs += 1
            if pf > best_pf:
                best_pf = pf
                best_params = p
                best_mdd = mdd
                
        if (i + 1) % 5 == 0:
            log.info(f"Tested {i+1}/{len(combinations)} configurations...")
            
    log.info("--- OPTIMIZATION COMPLETE ---")
    log.info(f"Found {valid_configs} parameter sets that passed the <10% Drawdown filter.")
    
    if best_params:
        log.info(f"🥇 BEST PARAMETERS: {best_params}")
        log.info(f"📈 Portfolio Avg Profit Factor: {best_pf:.2f}")
        log.info(f"🛡️ Portfolio Avg Max Drawdown: {best_mdd*100:.2f}%")
    else:
        log.warning("❌ No parameter set met the strict <10% Max Drawdown criteria.")

if __name__ == "__main__":
    run_multi_asset_optimizer()
