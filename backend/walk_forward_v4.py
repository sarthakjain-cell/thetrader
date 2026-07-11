import sqlite3
import pandas as pd
import numpy as np
from itertools import product
from datetime import timedelta
from strategy_v4 import StrategyV4
from logger import log

DB_PATH = "trading_system.db"

PARAM_GRID = {
    'fast_ema': [8, 10, 13],
    'slow_ema': [30, 40, 50],
    'rsi_thresh': [55, 60],
    'adx_thresh': [15, 20],
    'stop_atr_mult': [2.5, 3.0]
}

def load_multi_asset_data():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM market_data_1d ORDER BY Datetime ASC", conn)
    conn.close()
    df['Datetime'] = pd.to_datetime(df['Datetime'])
    return df

def apply_universe_rotation(df_all):
    """
    Computes 50-day momentum and tags the top 5 stocks each month.
    Adds an 'Entry_Allowed' boolean column to the dataframe.
    """
    # 1. Compute 50-day Momentum
    df_all['Mom_50'] = df_all.groupby('Symbol')['Close'].pct_change(periods=50)
    df_all['YearMonth'] = df_all['Datetime'].dt.to_period('M')
    
    # 2. Get the Momentum on the Last Trading Day of each month for each stock
    monthly_last_days = df_all.groupby(['Symbol', 'YearMonth'])['Datetime'].max().reset_index()
    monthly_last_days = pd.merge(monthly_last_days, df_all[['Symbol', 'Datetime', 'Mom_50']], on=['Symbol', 'Datetime'])
    
    # 3. This ranking is applied to the NEXT month
    monthly_last_days['TargetMonth'] = monthly_last_days['YearMonth'] + 1
    
    # 4. Rank stocks by Momentum descending within each TargetMonth
    monthly_last_days['Rank'] = monthly_last_days.groupby('TargetMonth')['Mom_50'].rank(ascending=False, method='first')
    
    # 5. Tag Top 5 with positive momentum
    monthly_last_days['Is_Top_5'] = (monthly_last_days['Rank'] <= 5) & (monthly_last_days['Mom_50'] > 0)
    
    # 6. Merge back onto the main dataframe
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
    
    for sym, sym_df in df_dict.items():
        if len(sym_df) < 100: continue
        
        strat = StrategyV4(sym_df, params)
        
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
    log.info("Applying Universe Rotation (50-Day Momentum, Top 5)...")
    df_all = apply_universe_rotation(df_all)
    
    symbols = df_all['Symbol'].unique()
    val_start, test_start = get_data_splits(df_all)
    
    df_dict = {sym: df_all[df_all['Symbol'] == sym].copy() for sym in symbols}
    
    keys, values = zip(*PARAM_GRID.items())
    combinations = [dict(zip(keys, v)) for v in product(*values)]
    
    log.info(f"Iteration 4 Grid Search: {len(combinations)} combinations.")
    log.info(f"Val Window:   {val_start.date()} -> {test_start.date()}")
    log.info(f"Test Window:  {test_start.date()} -> End")
    
    best_pf = 0
    best_params = None
    best_mdd = 1.0
    best_trades = 0
    
    for i, p in enumerate(combinations):
        pf, mdd, trades = evaluate_portfolio_on_window(df_dict, p, val_start, test_start)
        
        if mdd < 0.10 and trades >= 20:
            if pf > best_pf:
                best_pf = pf
                best_params = p
                best_mdd = mdd
                best_trades = trades
                
        if (i + 1) % 20 == 0:
            log.info(f"Val Tested {i+1}/{len(combinations)}...")
            
    log.info("--- OPTIMIZATION COMPLETE ---")
    if best_params:
        log.info(f"🥇 BEST VAL PARAMS: {best_params}")
        log.info(f"📈 VAL Portfolio PF: {best_pf:.2f} | MDD: {best_mdd*100:.2f}% | Trades: {best_trades}")
        
        test_end = df_all['Datetime'].max() + timedelta(days=1)
        t_pf, t_mdd, t_trades = evaluate_portfolio_on_window(df_dict, best_params, test_start, test_end)
        
        min_date = df_all['Datetime'].min()
        f_pf, f_mdd, f_trades = evaluate_portfolio_on_window(df_dict, best_params, min_date, test_end)
        
        log.info("\n=======================================================")
        log.info("🎓 FINAL EXAM: UNTOUCHED TEST WINDOW")
        log.info("=======================================================")
        log.info(f"Test Trades:            {t_trades}")
        log.info(f"Total 5-Yr Trades:      {f_trades}")
        log.info(f"Portfolio Profit Factor:{t_pf:.2f}")
        log.info(f"Portfolio Max Drawdown: {t_mdd*100:.2f}%")
        log.info("=======================================================\n")
        
        if t_pf > 1.5 and t_mdd < 0.10 and f_trades > 100:
            log.info("✅ SUCCESS! Strategy passes the Final Exam.")
        else:
            log.warning("❌ FAIL! Strategy degraded on Test Window.")
    else:
        log.warning("❌ No parameter set met the strict Val criteria (MDD < 10%, Trades >= 20).")

if __name__ == "__main__":
    run_multi_asset_optimizer()
