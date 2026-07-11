import sqlite3
import pandas as pd
import numpy as np
from datetime import timedelta
from strategy_v2 import StrategyV2
from logger import log

DB_PATH = "trading_system.db"
WINNING_PARAMS = {
    'fast_ema': 9,
    'slow_ema': 50,
    'rsi_thresh': 60,
    'adx_thresh': 20,
    'stop_atr_mult': 3.0
}

def load_test_data():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM market_data_1d ORDER BY Datetime ASC", conn)
    conn.close()
    df['Datetime'] = pd.to_datetime(df['Datetime'])
    
    max_date = df['Datetime'].max()
    cutoff_date = max_date - timedelta(days=365)
    return df, cutoff_date

def run_final_exam():
    df_all, cutoff_date = load_test_data()
    symbols = df_all['Symbol'].unique()
    
    log.info(f"Final Exam: Isolating Test Window (Last 365 Days) starting from {cutoff_date.date()}")
    
    results = []
    portfolio_equity_curve = None
    
    for sym in symbols:
        sym_df = df_all[df_all['Symbol'] == sym].copy()
        if len(sym_df) < 100: continue
        
        # 1. Initialize strategy on the FULL dataframe to pre-warm the moving averages
        strat = StrategyV2(sym_df, WINNING_PARAMS)
        
        # 2. Strict OOS Isolation: Slice the pre-warmed dataframe to ONLY trade in the last 365 days
        strat.df = strat.df[strat.df['Datetime'] >= cutoff_date].copy()
        
        if len(strat.df) < 50: continue
        
        # 3. Execute backtest
        res = strat.backtest(initial_capital=100000.0, risk_per_trade=0.01)
        
        # Align equity curves for true portfolio metrics
        eq_series = pd.Series(res.get('equity', [100000.0] * len(strat.df)))
        
        if portfolio_equity_curve is None:
            portfolio_equity_curve = eq_series
        else:
            # Padding if lengths mismatch slightly due to missing symbol data days
            min_len = min(len(portfolio_equity_curve), len(eq_series))
            portfolio_equity_curve = portfolio_equity_curve.iloc[:min_len] + eq_series.iloc[:min_len] - 100000.0
            
        results.append(res)
        
    if not results:
        log.error("No valid results computed.")
        return
        
    avg_pf = np.mean([r['pf'] for r in results])
    total_trades = sum(r['trades'] for r in results)
    
    # Portfolio Level Metrics
    rolling_max = portfolio_equity_curve.cummax()
    drawdowns = (portfolio_equity_curve - rolling_max) / rolling_max
    portfolio_mdd = abs(drawdowns.min())
    
    initial_port_cap = 100000.0 * len(results)
    final_port_cap = portfolio_equity_curve.iloc[-1] + (100000.0 * (len(results) - 1))
    port_ann_return = (final_port_cap - initial_port_cap) / initial_port_cap
    
    daily_returns = portfolio_equity_curve.pct_change().dropna()
    port_ann_vol = daily_returns.std() * np.sqrt(252)
    risk_free = 0.07
    
    sharpe = (port_ann_return - risk_free) / port_ann_vol if port_ann_vol > 0 else 0
    
    print("\n=======================================================")
    print("FINAL EXAM: UNTOUCHED TEST WINDOW (LAST 365 DAYS)")
    print("=======================================================")
    print(f"Total Trades:           {total_trades}")
    print(f"Portfolio Profit Factor:{avg_pf:.2f}")
    print(f"Portfolio Max Drawdown: {portfolio_mdd*100:.2f}%")
    print(f"Portfolio 1-Year Return:{port_ann_return*100:.2f}%")
    print(f"Portfolio Sharpe Ratio: {sharpe:.2f}")
    print("=======================================================\n")
    
    # Generate Jupyter Plot Code
    print("--- JUPYTER PLOT CODE (OOS EQUITY CURVE) ---")
    print("```python")
    print("import matplotlib.pyplot as plt")
    print(f"eq_curve = {portfolio_equity_curve.tolist()[::5]} # Sampled for brevity")
    print("plt.figure(figsize=(10,5))")
    print("plt.plot(eq_curve, color='blue', linewidth=2)")
    print("plt.title('Out-of-Sample Portfolio Equity Curve (Last 365 Days)')")
    print("plt.grid(True); plt.show()")
    print("```")

if __name__ == "__main__":
    run_final_exam()
