import time
import asyncio
import sqlite3
import pandas as pd
from datetime import datetime, time as dtime
from zoneinfo import ZoneInfo
from logger import log
from data_provider import YFinanceProvider
from feature_engine import compute_features

from strategy_001_orb import Strategy001ORB
from strategy_004_meanreversion import Strategy004MeanReversion

MARKET_OPEN = dtime(9, 15)
MARKET_CLOSE = dtime(15, 30)
SLEEP_INTERVAL_SECONDS = 60 # 1-minute tick
DB_PATH = "trading_system.db"
SYMBOLS = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS", "SBIN.NS"]
TOTAL_PAPER_CAPITAL = 1_000_000.0 # 10 Lakhs INR

def get_ist_now():
    return datetime.now(ZoneInfo('Asia/Kolkata'))

def is_market_open(now_time):
    if now_time.weekday() >= 5:
        return False
    return MARKET_OPEN <= now_time.time() <= MARKET_CLOSE

class MetaAllocator:
    def __init__(self, total_capital: float):
        self.total_capital = total_capital
        
    def allocate(self, intents: list, open_positions_count: int) -> list:
        """
        Deduplicates intents and allocates capital.
        intents format: [{"symbol": "REL", "strategy_id": "S1", "conviction": 0.8, "signal_dict": {...}}, ...]
        """
        if not intents:
            return []
            
        # 1. Deduplicate by symbol, keeping the one with highest conviction
        deduped = {}
        for intent in intents:
            sym = intent["symbol"]
            if sym not in deduped or intent["conviction"] > deduped[sym]["conviction"]:
                deduped[sym] = intent
                
        approved_trades = []
        # Max open positions across the portfolio (e.g. 5)
        max_positions = 5
        available_slots = max_positions - open_positions_count
        
        if available_slots <= 0:
            log.warning("MetaAllocator Veto: Portfolio is full (max 5 positions).")
            return []
            
        # Sort remaining intents by conviction descending
        sorted_intents = sorted(deduped.values(), key=lambda x: x["conviction"], reverse=True)
        
        # Take only the top N that we have slots for
        selected_intents = sorted_intents[:available_slots]
        
        # Allocate capital (10% of total capital per trade = 100k)
        allocation_per_trade = self.total_capital * 0.10
        
        for intent in selected_intents:
            price = intent["price"]
            qty = int(allocation_per_trade / price)
            if qty > 0:
                intent["allocated_qty"] = qty
                approved_trades.append(intent)
                
        return approved_trades

class MultiStrategyEngine:
    def __init__(self):
        self.provider = YFinanceProvider()
        # Load Hardcoded strategies
        self.strategies = [
            Strategy001ORB(),
            Strategy004MeanReversion()
        ]
        
        # Load Generated Strategies
        conn = self._get_db()
        try:
            from dynamic_strategy import DynamicStrategy
            import json
            
            df = pd.read_sql("SELECT strategy_id, config_json FROM generated_strategies", conn)
            for _, row in df.iterrows():
                try:
                    dyn_strat = DynamicStrategy(row['config_json'])
                    self.strategies.append(dyn_strat)
                    log.info(f"Loaded Dynamic Strategy: {row['strategy_id']}")
                except Exception as e:
                    log.error(f"Failed to load dynamic strategy {row['strategy_id']}: {e}")
        except Exception as e:
            log.warning(f"Could not load generated strategies: {e}")
        finally:
            conn.close()
            
        self.allocator = MetaAllocator(TOTAL_PAPER_CAPITAL)
        log.info(f"Initialized Engine with {len(self.strategies)} total strategies. MetaAllocator active.")
        
    def _get_db(self):
        return sqlite3.connect(DB_PATH)

    def fetch_market_data(self):
        data = {}
        for sym in SYMBOLS:
            df = self.provider.get_today_data(sym)
            if not df.empty:
                # Pre-compute features immediately upon fetching
                try:
                    df = compute_features(df)
                    data[sym] = df
                except Exception as e:
                    log.error(f"Feature computation failed for {sym}: {e}")
        return data
        
    def fetch_context(self):
        conn = self._get_db()
        context = {"sentiment": {}, "macro_alerts": []}
        try:
            today_str = get_ist_now().strftime('%Y-%m-%d')
            
            # Fetch latest sentiment (hourly grouped)
            df_sent = pd.read_sql(f"SELECT symbol, avg_compound FROM sentiment_scores WHERE date='{today_str}'", conn)
            if not df_sent.empty:
                # Group by symbol and take the mean of the day's hourly scores
                agg_sent = df_sent.groupby('symbol')['avg_compound'].mean().to_dict()
                context["sentiment"] = agg_sent
                
            # Fetch active macro alerts
            df_macro = pd.read_sql(f"SELECT theme_name, negative_stocks FROM macro_alerts WHERE expiry_date >= '{today_str}'", conn)
            if not df_macro.empty:
                neg_stocks = set()
                for _, row in df_macro.iterrows():
                    context["macro_alerts"].append(row["theme_name"])
                    if row["negative_stocks"]:
                        for s in row["negative_stocks"].split(","):
                            neg_stocks.add(s.strip())
                context["active_negative_stocks"] = neg_stocks
                
        except Exception as e:
            log.error(f"Failed to fetch context: {e}")
        finally:
            conn.close()
            
        return context
        
    def process_tick(self, now):
        data = self.fetch_market_data()
        context = self.fetch_context()
        
        conn = self._get_db()
        positions_df = pd.read_sql("SELECT * FROM paper_positions", conn)
        cursor = conn.cursor()
        
        raw_intents = []
        open_positions_count = len(positions_df)
        
        # Phase 1: Evaluate Strategies and Manage Positions
        for strategy in self.strategies:
            strat_id = strategy.strategy_id
            strat_pos = positions_df[positions_df['strategy_id'] == strat_id]
            
            for sym, df in data.items():
                current_bar = df.iloc[-1]
                pos = strat_pos[strat_pos['symbol'] == sym]
                
                if not pos.empty:
                    # Manage existing position
                    p = pos.iloc[0]
                    res = strategy.manage_position(sym, p.to_dict(), current_bar)
                    
                    if res.get("action") == "UPDATE_STOP":
                        new_stop = res["new_stop"]
                        cursor.execute("UPDATE paper_positions SET stop_loss=? WHERE id=?", (new_stop, int(p['id'])))
                        log.info(f"[{strat_id}] TRAIL STOP {sym} to {new_stop:.2f}")
                        
                    elif res.get("action") == "CLOSE":
                        exit_price = res.get("exit_price", current_bar['Close'])
                        trade_value = p['qty'] * exit_price
                        pnl = trade_value - (p['qty'] * p['entry_price'])
                        
                        cursor.execute("DELETE FROM paper_positions WHERE id=?", (int(p['id']),))
                        cursor.execute("""
                            INSERT INTO paper_trades (symbol, strategy_id, entry_time, exit_time, entry_price, exit_price, qty, pnl, reason, notes)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (sym, strat_id, p['entry_time'], now.strftime('%Y-%m-%d %H:%M:%S'), p['entry_price'], exit_price, int(p['qty']), pnl, res['reason'], ""))
                        log.info(f"[{strat_id}] CLOSED {sym}: {res['reason']} | PnL: {pnl:.2f}")
                        # Reduce count immediately to free slot
                        open_positions_count -= 1 
                else:
                    # Evaluate new signals
                    signal_dict = strategy.evaluate(sym, current_bar, context)
                    if signal_dict["signal"] == "BUY":
                        raw_intents.append({
                            "symbol": sym,
                            "strategy_id": strat_id,
                            "conviction": signal_dict.get("conviction", 0.5),
                            "price": current_bar['Close'],
                            "signal_dict": signal_dict
                        })
                        
        # Phase 2: Meta-Allocator filters and sizes intents
        if raw_intents:
            log.info(f"MetaAllocator evaluating {len(raw_intents)} raw intents...")
            approved_trades = self.allocator.allocate(raw_intents, open_positions_count)
            
            for trade in approved_trades:
                sym = trade["symbol"]
                strat_id = trade["strategy_id"]
                price = trade["price"]
                qty = trade["allocated_qty"]
                sd = trade["signal_dict"]
                
                cursor.execute("""
                    INSERT INTO paper_positions (symbol, strategy_id, entry_time, entry_price, qty, stop_loss, target)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (sym, strat_id, now.strftime('%Y-%m-%d %H:%M:%S'), price, qty, sd["stop_loss"], sd["target"]))
                
                log.info(f"[{strat_id}] ALLOCATED BUY {sym} | Qty: {qty} @ {price:.2f} | Reason: {sd['reason']}")
                
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
                    error_msg = f"Fatal Error in live_trader main loop: {str(e)}"
                    log.error(error_msg)
                    try:
                        from discord_alert import send_discord_alert
                        send_discord_alert(f"```\n{error_msg}\n```", "🚨 FATAL CRASH: live_trader", 0xff0000)
                    except:
                        pass
                    import time
                    time.sleep(60)
                
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
