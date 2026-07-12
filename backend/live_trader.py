import time
import asyncio
import sqlite3
import pandas as pd
from datetime import datetime, time as dtime
from zoneinfo import ZoneInfo
from logger import log
from data_provider import YFinanceProvider
import os

from strategy_001_orb import Strategy001ORB
from strategy_002_vwap import Strategy002VWAP

MARKET_OPEN = dtime(9, 15)
MARKET_CLOSE = dtime(15, 30)
SLEEP_INTERVAL_SECONDS = 60 # 1-minute tick
DB_PATH = "trading_system.db"
SYMBOLS = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS", "SBIN.NS"]

def get_ist_now():
    return datetime.now(ZoneInfo('Asia/Kolkata'))

def is_market_open(now_time):
    if now_time.weekday() >= 5:
        return False
    return MARKET_OPEN <= now_time.time() <= MARKET_CLOSE

class MultiStrategyEngine:
    def __init__(self):
        self.provider = YFinanceProvider()
        self.strategies = [
            Strategy001ORB(),
            Strategy002VWAP()
        ]
        log.info(f"Initialized Engine with {len(self.strategies)} strategies.")
        
    def _get_db(self):
        return sqlite3.connect(DB_PATH)

    def fetch_market_data(self):
        data = {}
        for sym in SYMBOLS:
            df = self.provider.get_today_data(sym)
            if not df.empty:
                data[sym] = df
        return data
        
    def process_tick(self, now):
        data = self.fetch_market_data()
        context = {} # Future: Add NLP flags here
        
        conn = self._get_db()
        positions_df = pd.read_sql("SELECT * FROM paper_positions", conn)
        cursor = conn.cursor()
        
        for strategy in self.strategies:
            strat_id = strategy.strategy_id
            strat_pos = positions_df[positions_df['strategy_id'] == strat_id]
            
            for sym, df in data.items():
                pos = strat_pos[strat_pos['symbol'] == sym]
                
                if not pos.empty:
                    # Manage existing position
                    p = pos.iloc[0]
                    res = strategy.manage_position(sym, p.to_dict(), df)
                    if res["action"] == "CLOSE":
                        exit_price = res["exit_price"]
                        trade_value = p['qty'] * exit_price
                        pnl = trade_value - (p['qty'] * p['entry_price']) # Ignoring brokerage for now
                        
                        cursor.execute("DELETE FROM paper_positions WHERE id=?", (int(p['id']),))
                        cursor.execute("""
                            INSERT INTO paper_trades (symbol, strategy_id, entry_time, exit_time, entry_price, exit_price, qty, pnl, reason, notes)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (sym, strat_id, p['entry_time'], now.strftime('%Y-%m-%d %H:%M:%S'), p['entry_price'], exit_price, int(p['qty']), pnl, res['reason'], ""))
                        log.info(f"[{strat_id}] CLOSED {sym}: {res['reason']} | PnL: {pnl:.2f}")
                else:
                    # Evaluate new signals
                    signal_dict = strategy.evaluate(sym, df, context)
                    if signal_dict["signal"] == "BUY":
                        price = df.iloc[-1]['Close']
                        qty = 10 # Fixed qty for paper trading testing
                        stop_loss = signal_dict["stop_loss"]
                        target = signal_dict["target"]
                        
                        cursor.execute("""
                            INSERT INTO paper_positions (symbol, strategy_id, entry_time, entry_price, qty, stop_loss, target)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (sym, strat_id, now.strftime('%Y-%m-%d %H:%M:%S'), price, qty, stop_loss, target))
                        
                        log.info(f"[{strat_id}] ENTERED {sym} BUY @ {price:.2f} | Reason: {signal_dict['reason']}")
                        
        conn.commit()
        conn.close()

async def trading_loop():
    engine = MultiStrategyEngine()
    last_tick_time = None

    while True:
        now = get_ist_now()
        
        if is_market_open(now):
            if last_tick_time is None or (now - last_tick_time).total_seconds() >= SLEEP_INTERVAL_SECONDS:
                log.info(f"[{now.strftime('%H:%M:%S')}] Firing tick to {len(engine.strategies)} strategies...")
                try:
                    engine.process_tick(now)
                    last_tick_time = now
                except Exception as e:
                    log.error(f"Error processing tick: {e}")
                
            await asyncio.sleep(5)
        else:
            if now.time() < MARKET_OPEN and now.weekday() < 5:
                await asyncio.sleep(60)
            else:
                await asyncio.sleep(3600)

if __name__ == "__main__":
    try:
        asyncio.run(trading_loop())
    except KeyboardInterrupt:
        log.info("Live Paper Trader stopped manually.")
