import sqlite3
import pandas as pd
from datetime import datetime
from data_provider import DataProvider
from paper_trader import PaperTrader
from init_paper_db import init_paper_db
from logger import log

class SimulatedDataProvider(DataProvider):
    def __init__(self, df_day):
        self.df_day = df_day.copy()
        self.df_day['Datetime'] = pd.to_datetime(self.df_day['Datetime'])
        self.current_time = None
        
    def get_today_data(self, symbol):
        if self.current_time is None: return pd.DataFrame()
        mask = self.df_day['Datetime'] <= self.current_time
        return self.df_day[mask & (self.df_day['Symbol'] == symbol)].copy()

def reset_db():
    conn = sqlite3.connect("trading_system.db")
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS paper_account")
    cursor.execute("DROP TABLE IF EXISTS paper_positions")
    cursor.execute("DROP TABLE IF EXISTS paper_trades")
    cursor.execute("DROP TABLE IF EXISTS daily_summary")
    conn.commit()
    conn.close()
    init_paper_db()

def run_verification(target_day_index=55):
    reset_db()
    
    conn = sqlite3.connect("trading_system.db")
    df_all = pd.read_sql("SELECT * FROM market_data_5m ORDER BY Datetime ASC", conn)
    conn.close()
    
    df_all['Datetime'] = pd.to_datetime(df_all['Datetime'])
    df_all['Date'] = df_all['Datetime'].dt.date
    
    unique_dates = sorted(df_all['Date'].unique())
    if len(unique_dates) <= target_day_index:
        log.warning(f"Not enough days to simulate day {target_day_index}")
        return
        
    target_date = unique_dates[target_day_index]
    log.info(f"--- Simulating Historical Day: {target_date} ---")
    
    df_day = df_all[df_all['Date'] == target_date].copy()
    
    sim_provider = SimulatedDataProvider(df_day)
    trader = PaperTrader(sim_provider, is_live=False)
    
    # 09:15 to 15:30
    times = sorted(df_day['Datetime'].unique())
    
    for t in times:
        # PaperTrader processes tick on the close of the candle.
        # e.g., if candle is 09:15, it closes at 09:20. We simulate being at 09:20.
        # Since 'Datetime' in yfinance is the start of the candle, we just pass the candle time to let the provider fetch up to it.
        # So when t = 09:15, provider returns up to 09:15.
        sim_provider.current_time = t
        trader.process_tick(t)
        
    # Print results
    conn = sqlite3.connect("trading_system.db")
    trades = pd.read_sql("SELECT * FROM paper_trades", conn)
    acc = pd.read_sql("SELECT * FROM paper_account WHERE id=1", conn).iloc[0]
    conn.close()
    
    log.info(f"Final Equity: ₹{acc['equity']:.2f}")
    log.info(f"Total Trades: {len(trades)}")
    
    if not trades.empty:
        log.info("Trades Ledger:")
        print(trades[['symbol', 'entry_time', 'exit_time', 'pnl', 'reason']])
    
    log.info("Verification Complete.")

if __name__ == "__main__":
    run_verification(55)
