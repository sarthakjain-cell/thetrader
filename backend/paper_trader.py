import sqlite3
import time
import pandas as pd
import numpy as np
import ta
from datetime import datetime, time as dtime
from zoneinfo import ZoneInfo
from logger import log
from data_provider import YFinanceProvider

DB_PATH = "trading_system.db"
NIFTY_SYMBOLS = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS",
    "KOTAKBANK.NS", "AXISBANK.NS", "SBIN.NS", "BAJFINANCE.NS", "ITC.NS",
    "LT.NS", "BHARTIARTL.NS", "HINDUNILVR.NS"
]

class PaperTrader:
    def __init__(self, data_provider, is_live=True):
        self.provider = data_provider
        self.is_live = is_live
        self.best_orb = {'orb_bars': 6, 'orb_target': 2.0, 'orb_stop': 1.0}
        self.symbols = NIFTY_SYMBOLS
        self.today_date = None
        self.regimes = {} # symbol -> regime
        self.orb_highs = {} # symbol -> high
        self.avg_5m_ranges = {} # symbol -> avg range
        
        # Risk Limits
        self.max_daily_loss_pct = 0.02
        self.max_peak_drawdown_pct = 0.10
        self.risk_per_trade = 0.01
        
        # Load historical context once
        self._load_historical_context()

    def _get_db(self):
        return sqlite3.connect(DB_PATH)

    def _load_historical_context(self):
        log.info("Loading historical context for 10-day averages...")
        conn = self._get_db()
        df_hist = pd.read_sql("SELECT * FROM market_data_5m ORDER BY Datetime ASC", conn)
        conn.close()
        
        df_hist['Datetime'] = pd.to_datetime(df_hist['Datetime'])
        df_hist['Date'] = df_hist['Datetime'].dt.date
        
        self.historical_data = df_hist

    def _init_daily_state(self, current_date):
        self.today_date = current_date
        self.regimes = {}
        self.orb_highs = {}
        self.avg_5m_ranges = {}
        
        # Load AI Forecasts and Threshold
        conn = self._get_db()
        self.ai_forecasts = {}
        self.ai_rationales = {}
        self.ai_threshold = 0.55
        self.ai_active = True
        self.trend_scores = {}
        self.market_regime_multiplier = 1.0
        
        # Load Trend Scores
        trends = pd.read_sql(f"SELECT * FROM multi_timeframe_trends WHERE date='{current_date}'", conn)
        if not trends.empty:
            for _, row in trends.iterrows():
                self.trend_scores[row['symbol']] = row['trend_score']
                
        # Load Market Regime Multiplier
        config_regime = pd.read_sql("SELECT * FROM model_config WHERE key='market_regime_multiplier'", conn)
        if not config_regime.empty:
            self.market_regime_multiplier = float(config_regime.iloc[0]['value'])
            
        forecasts = pd.read_sql(f"SELECT * FROM research_tips WHERE date='{current_date}'", conn)
        if not forecasts.empty:
            for _, row in forecasts.iterrows():
                self.ai_forecasts[row['symbol']] = row['score']
                self.ai_rationales[row['symbol']] = row['rationale']
                
            config = pd.read_sql("SELECT * FROM model_config WHERE key='ai_conviction_threshold'", conn)
            if not config.empty:
                self.ai_threshold = float(config.iloc[0]['value'])
                
            config_active = pd.read_sql("SELECT * FROM model_config WHERE key='ai_active'", conn)
            if not config_active.empty:
                self.ai_active = int(config_active.iloc[0]['value']) == 1
                
            if not self.ai_active:
                log.warning("AI Meta-Layer is deactivated due to recent drift. Falling back to un-filtered ORB.")
        else:
            log.warning("No AI Forecasts found for today. Falling back to unfiltered ORB.")
            self.ai_active = False
            
        conn.close()
        log.info(f"Initialized daily state for {current_date}")
        
    def _check_risk_halts(self):
        conn = self._get_db()
        acc = pd.read_sql("SELECT * FROM paper_account WHERE id=1", conn).iloc[0]
        # Calculate Total Portfolio Value
        positions = pd.read_sql("SELECT * FROM paper_positions", conn)
        total_equity = acc['equity']
        for _, pos in positions.iterrows():
            df = self.provider.get_today_data(pos['symbol'])
            if not df.empty:
                total_equity += pos['qty'] * df.iloc[-1]['Close']
                
        conn.close()
        
        if acc['is_halted']:
            return True, "GLOBAL_HALT"
            
        # Update peak equity if needed
        if total_equity > acc['peak_equity']:
            conn = self._get_db()
            cursor = conn.cursor()
            cursor.execute("UPDATE paper_account SET peak_equity=? WHERE id=1", (total_equity,))
            conn.commit()
            conn.close()
            acc['peak_equity'] = total_equity
            
        mdd = (acc['peak_equity'] - total_equity) / acc['peak_equity']
        if mdd >= self.max_peak_drawdown_pct:
            log.warning("🚨 GLOBAL KILL SWITCH TRIGGERED: 10% MDD HIT!")
            self._halt_account()
            return True, "GLOBAL_HALT"
            
        # Check daily floor
        conn = self._get_db()
        summary = pd.read_sql("SELECT * FROM daily_summary ORDER BY date DESC LIMIT 1", conn)
        conn.close()
        if not summary.empty:
            start_equity = summary.iloc[0]['end_equity']
            daily_loss = (start_equity - total_equity) / start_equity
            if daily_loss >= self.max_daily_loss_pct:
                log.warning("⚠️ DAILY LOSS LIMIT (2%) HIT! Halting new entries for today.")
                return True, "DAILY_HALT"
                
        return False, "OK"
        
    def _halt_account(self):
        conn = self._get_db()
        cursor = conn.cursor()
        cursor.execute("UPDATE paper_account SET is_halted = 1 WHERE id=1")
        conn.commit()
        conn.close()
        self.liquidate_all("global_halt")

    def liquidate_all(self, reason, current_time=None):
        if current_time is None:
            current_time = datetime.now(ZoneInfo('Asia/Kolkata'))
            
        conn = self._get_db()
        cursor = conn.cursor()
        positions = pd.read_sql("SELECT * FROM paper_positions", conn)
        
        for _, pos in positions.iterrows():
            # If EOD liquidation, skip DELIVERY trades
            if reason == "eod_stop" and pos.get('trade_type', 'INTRADAY') == 'DELIVERY':
                continue
                
            sym = pos['symbol']
            # Fetch current price
            df = self.provider.get_today_data(sym)
            if df.empty: continue
            
            close_price = df.iloc[-1]['Close']
            qty = pos['qty']
            entry_price = pos['entry_price']
            
            # Simulated exit slippage/fees
            exit_price = close_price * (1 - 0.0005) # fixed slippage for market close
            trade_value = qty * exit_price
            brokerage = min(trade_value * 0.0005, 20.0) + (trade_value * 0.00025)
            pnl = trade_value - brokerage - (qty * entry_price)
            
            cursor.execute("DELETE FROM paper_positions WHERE id=?", (pos['id'],))
            cursor.execute("""
                INSERT INTO paper_trades (symbol, entry_time, exit_time, entry_price, exit_price, qty, pnl, reason, notes, trade_type)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (sym, pos['entry_time'], current_time.strftime('%Y-%m-%d %H:%M:%S'), entry_price, exit_price, qty, pnl, reason, "EOD Liquidation", pos.get('trade_type', 'INTRADAY')))
            
            # Update account
            cursor.execute("UPDATE paper_account SET equity = equity + ? WHERE id=1", (trade_value - brokerage,))
            
        conn.commit()
        conn.close()
        log.info(f"Liquidated positions. Reason: {reason}")
        
    def _compute_dynamic_slippage(self, range_pct, avg_range_pct):
        baseline = 0.0005
        if avg_range_pct == 0: return baseline
        excess_pct = max(0, (range_pct / avg_range_pct) - 1.0) * 100
        additional = excess_pct * 0.0001
        return baseline + additional

    def evaluate_stock(self, sym, df, active_negative_stocks, active_positive_stocks):
        latest_bar = df.iloc[-1]
        price = latest_bar['Close']
        
        # Calculate some basic TA for the scanner even if not purely used for ORB entry
        rsi = 50.0
        adx = 25.0
        vol_spike = 1.0
        
        df_ta = df.copy()
        if len(df_ta) >= 14:
            rsi = ta.momentum.RSIIndicator(df_ta['Close'], window=14).rsi().iloc[-1]
            adx = ta.trend.ADXIndicator(df_ta['High'], df_ta['Low'], df_ta['Close'], window=14).adx().iloc[-1]
            avg_vol = df_ta['Volume'].rolling(10).mean().iloc[-1]
            vol_spike = latest_bar['Volume'] / avg_vol if avg_vol > 0 else 1.0

        signal = "HOLD"
        confidence = "Neutral"
        reason = "No setup met."
        sentiment = 0.0

        if sym in active_positive_stocks:
            sentiment = 0.5
            confidence = "High"
        elif sym in active_negative_stocks:
            sentiment = -0.5
            confidence = "Low"

        regime = self.regimes.get(sym, "WAITING")
        trend_score = self.trend_scores.get(sym, 50)
        
        if regime == 'ORB' and sym in self.orb_highs:
            if price > self.orb_highs[sym]:
                # Multi-Timeframe Trend Veto
                if trend_score == 0:
                    signal = "VETO"
                    reason = f"TREND VETO: Multi-Timeframe alignment is LOW (Score 0). Fighting the trend."
                    return {
                        'symbol': sym, 'last_price': price, 'regime': regime, 'signal': signal,
                        'rsi': rsi, 'volume_spike': vol_spike, 'adx': adx, 'sentiment': sentiment,
                        'confidence': confidence, 'reason': reason
                    }
                    
                # Check AI Gate
                if self.ai_active and sym in self.ai_forecasts:
                    prob = self.ai_forecasts[sym]
                    if prob < 0:
                        signal = "VETO"
                        reason = f"AI VETO: Gemini Sentiment is negative ({prob:.2f}). Rationale: {self.ai_rationales.get(sym, '')}"
                        return {
                            'symbol': sym, 'last_price': price, 'regime': regime, 'signal': signal,
                            'rsi': rsi, 'volume_spike': vol_spike, 'adx': adx, 'sentiment': sentiment,
                            'confidence': confidence, 'reason': reason
                        }
                        
                if sym in active_negative_stocks:
                    signal = "VETO"
                    reason = f"MACRO VETO: Blocked ORB Buy for {sym} due to active global headwind."
                else:
                    signal = "BUY"
                    reason = f"ORB Breakout confirmed at {price:.2f}. Volume {vol_spike:.1f}x avg, RSI: {rsi:.1f}."
                    if self.ai_active and sym in self.ai_forecasts:
                        reason += f" AI Conviction: {self.ai_forecasts[sym]:.2f}."
            else:
                reason = f"Waiting for breakout above {self.orb_highs[sym]:.2f}"
                
        return {
            'symbol': sym,
            'last_price': price,
            'regime': regime,
            'signal': signal,
            'rsi': rsi,
            'volume_spike': vol_spike,
            'adx': adx,
            'sentiment': sentiment,
            'confidence': confidence,
            'reason': reason
        }

    def process_tick(self, current_time=None):
        if current_time is None:
            current_time = datetime.now(ZoneInfo('Asia/Kolkata'))
            
        current_date = current_time.date()
        
        if self.today_date != current_date:
            self._init_daily_state(current_date)
            
        halted, halt_reason = self._check_risk_halts()
        if halt_reason == "GLOBAL_HALT":
            return
            
        # EOD Liquidation
        if current_time.time() >= dtime(15, 25):
            self.liquidate_all("eod_stop", current_time)
            # Write daily summary
            conn = self._get_db()
            acc = pd.read_sql("SELECT * FROM paper_account WHERE id=1", conn).iloc[0]
            trades_today = pd.read_sql(f"SELECT COUNT(*) FROM paper_trades WHERE exit_time LIKE '{current_date}%'", conn).iloc[0,0]
            pnl_today = pd.read_sql(f"SELECT SUM(pnl) FROM paper_trades WHERE exit_time LIKE '{current_date}%'", conn).iloc[0,0]
            if pd.isna(pnl_today): pnl_today = 0
            
            cursor = conn.cursor()
            cursor.execute("INSERT OR REPLACE INTO daily_summary (date, end_equity, daily_pnl, trades_count, peak_drawdown) VALUES (?, ?, ?, ?, ?)",
                (str(current_date), acc['equity'], pnl_today, int(trades_today), (acc['peak_equity'] - acc['equity'])/acc['peak_equity']))
            conn.commit()
            conn.close()
            return
            
        conn = self._get_db()
        positions = pd.read_sql("SELECT * FROM paper_positions", conn)
        acc = pd.read_sql("SELECT * FROM paper_account WHERE id=1", conn).iloc[0]
        
        # Load active Macro Alerts
        current_date_str = current_time.strftime('%Y-%m-%d')
        macro_alerts = pd.read_sql(f"SELECT * FROM macro_alerts WHERE expiry_date >= '{current_date_str}'", conn)
        
        active_negative_stocks = set()
        active_positive_stocks = set()
        
        for _, alert in macro_alerts.iterrows():
            if alert['negative_stocks']:
                active_negative_stocks.update(alert['negative_stocks'].split(','))
            if alert['positive_stocks']:
                active_positive_stocks.update(alert['positive_stocks'].split(','))
                
        cursor = conn.cursor()
        
        for sym in self.symbols:
            df = self.provider.get_today_data(sym)
            if df.empty: continue
            
            # Compute 10d avg opening range from historical
            hist_sym = self.historical_data[self.historical_data['Symbol'] == sym]
            if sym not in self.regimes and len(df) >= 1:
                # 09:15-09:20 bar is complete
                first_bar = df.iloc[0]
                first_range = first_bar['High'] - first_bar['Low']
                
                # Get historical daily opening ranges
                daily_firsts = hist_sym.groupby('Date').first()
                if len(daily_firsts) >= 10:
                    avg_opening_range = (daily_firsts['High'] - daily_firsts['Low']).tail(10).mean()
                    prev_close = daily_firsts['Close'].iloc[-1]
                else:
                    avg_opening_range = float('inf')
                    prev_close = first_bar['Open']
                    
                # Determine Regime
                if first_range > avg_opening_range and first_bar['Close'] > first_bar['Open']:
                    self.regimes[sym] = 'ORB'
                else:
                    self.regimes[sym] = 'VWAP'
                    
                log.info(f"{sym} Regime Set: {self.regimes[sym]}")
                
            if sym not in self.avg_5m_ranges and not hist_sym.empty:
                self.avg_5m_ranges[sym] = ((hist_sym['High'] - hist_sym['Low']) / hist_sym['Close']).mean()
                
            # If in ORB regime, wait for 30m ORB to form (6 bars)
            if self.regimes.get(sym) == 'ORB' and len(df) >= self.best_orb['orb_bars']:
                if sym not in self.orb_highs:
                    self.orb_highs[sym] = df.iloc[:self.best_orb['orb_bars']]['High'].max()
                    log.info(f"{sym} ORB High Set: {self.orb_highs[sym]}")
                    
            latest_bar = df.iloc[-1]
            price = latest_bar['Close']
            high = latest_bar['High']
            low = latest_bar['Low']
            
            # Position Management
            pos = positions[positions['symbol'] == sym]
            if not pos.empty:
                p = pos.iloc[0]
                exit_price = None
                reason = None
                
                # --- Trailing Stop-Loss Logic (1R Step) ---
                risk_dist = p['entry_price'] - p['stop_loss']
                if risk_dist > 0: # Long position
                    # If price has moved 1R in our favor, move stop to Breakeven
                    if high >= (p['entry_price'] + risk_dist) and p['stop_loss'] < p['entry_price']:
                        new_stop = p['entry_price']
                        cursor.execute("UPDATE paper_positions SET stop_loss=? WHERE id=?", (new_stop, int(p['id'])))
                        conn.commit()
                        log.info(f"Trailing Stop Triggered for {sym}: Moved Stop to Breakeven ({new_stop:.2f})")
                        p['stop_loss'] = new_stop # Update local reference for the tick evaluate
                
                if low <= p['stop_loss']:
                    exit_price = min(latest_bar['Open'], p['stop_loss'])
                    reason = "stop"
                elif high >= p['target']:
                    exit_price = max(latest_bar['Open'], p['target'])
                    reason = "target"
                    
                if exit_price is not None:
                    trade_value = p['qty'] * exit_price
                    brokerage = min(trade_value * 0.0005, 20.0) + (trade_value * 0.00025)
                    pnl = trade_value - brokerage - (p['qty'] * p['entry_price'])
                    
                    cursor.execute("DELETE FROM paper_positions WHERE id=?", (int(p['id']),))
                    cursor.execute("""
                        INSERT INTO paper_trades (symbol, entry_time, exit_time, entry_price, exit_price, qty, pnl, reason, notes, trade_type)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (sym, p['entry_time'], current_time.strftime('%Y-%m-%d %H:%M:%S'), p['entry_price'], exit_price, int(p['qty']), pnl, reason, "Target/Stop Hit", p.get('trade_type', 'INTRADAY')))
                    
                    new_equity = acc['equity'] + trade_value - brokerage
                    new_peak = max(acc['peak_equity'], new_equity)
                    cursor.execute("UPDATE paper_account SET equity=?, peak_equity=? WHERE id=1", (new_equity, new_peak))
                    acc['equity'] = new_equity
                    acc['peak_equity'] = new_peak
                    log.info(f"Closed {sym}: {reason} | PnL: {pnl:.2f}")
                    continue
                    
            # Evaluate Signal
            eval_data = self.evaluate_stock(sym, df, active_negative_stocks, active_positive_stocks)
            
            # Upsert into market_signals
            cursor.execute("""
                INSERT OR REPLACE INTO market_signals (symbol, last_price, regime, signal, rsi, volume_spike, adx, sentiment, confidence, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (sym, eval_data['last_price'], eval_data['regime'], eval_data['signal'], eval_data['rsi'], eval_data['volume_spike'], eval_data['adx'], eval_data['sentiment'], eval_data['confidence'], current_time.strftime('%Y-%m-%d %H:%M:%S')))
            
            # Entry Logic (If no position and not halted)
            if pos.empty and not halted:
                if eval_data['signal'] == 'VETO':
                    cursor.execute("""
                        INSERT INTO paper_trades (symbol, entry_time, exit_time, entry_price, exit_price, qty, pnl, reason, notes, trade_type)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (sym, current_time.strftime('%Y-%m-%d %H:%M:%S'), current_time.strftime('%Y-%m-%d %H:%M:%S'), price, price, 0, 0.0, "macro_veto", eval_data['reason'], 'INTRADAY'))
                    continue
                    
                if eval_data['signal'] == 'BUY':
                    # Calculate ATR for stop
                    df_ta = df.copy()
                    if len(df_ta) >= 14:
                        atr = ta.volatility.AverageTrueRange(df_ta['High'], df_ta['Low'], df_ta['Close'], window=14).average_true_range().iloc[-1]
                        
                        range_pct = (latest_bar['High'] - latest_bar['Low']) / price
                        avg_range_pct = self.avg_5m_ranges.get(sym, 0.005)
                        slippage_rate = self._compute_dynamic_slippage(range_pct, avg_range_pct)
                        
                        exec_price = price * (1 + slippage_rate)
                        stop_dist = atr * self.best_orb['orb_stop']
                        
                        if stop_dist > 0:
                                    
                                risk_to_use = self.risk_per_trade
                                multiplier_used = 1.0
                                
                                # Apply Linear Fractional Sizing based on Multi-Timeframe Trend and Conviction
                                ml_prob = self.ai_forecasts.get(sym, self.ai_threshold) if self.ai_active else self.ai_threshold
                                trend_score = self.trend_scores.get(sym, 50)
                                
                                # Formula: base_risk * (trend / 100) * (ml_prob / threshold) * market_regime_multiplier
                                dynamic_risk = self.risk_per_trade * (trend_score / 100.0) * (ml_prob / self.ai_threshold) * self.market_regime_multiplier
                                
                                # Cap it at 1% max per instruction
                                risk_to_use = min(dynamic_risk, self.risk_per_trade)
                                multiplier_used = dynamic_risk / self.risk_per_trade if self.risk_per_trade > 0 else 1.0
                                        
                                if sym in active_positive_stocks:
                                    # Still apply macro boost, but cap at 1% max per instructions
                                    multiplier_used *= 1.5
                                    risk_to_use = min(risk_to_use * 1.5, self.risk_per_trade)
                                    log.info(f"MACRO CONVICTION: Increased risk multiplier for {sym} due to tailwind.")
                                
                                risk_amt = acc['equity'] * risk_to_use
                                qty = int(risk_amt / stop_dist)
                                max_qty = int(acc['equity'] / exec_price)
                                qty = min(qty, max_qty)
                                
                                if qty > 0:
                                    trade_value = qty * exec_price
                                    brokerage = min(trade_value * 0.0005, 20.0)
                                    
                                    new_equity = acc['equity'] - trade_value - brokerage
                                    cursor.execute("UPDATE paper_account SET equity=? WHERE id=1", (new_equity,))
                                    acc['equity'] = new_equity
                                    
                                    stop_loss = exec_price - stop_dist
                                    target = exec_price + (atr * self.best_orb['orb_target'])
                                    
                                    cursor.execute("""
                                        INSERT INTO paper_positions (symbol, entry_time, entry_price, qty, stop_loss, target, trade_type)
                                        VALUES (?, ?, ?, ?, ?, ?, ?)
                                    """, (sym, current_time.strftime('%Y-%m-%d %H:%M:%S'), exec_price, qty, stop_loss, target, 'INTRADAY' if self.regimes.get(sym) == 'ORB' else 'DELIVERY'))
                                    
                                    # Log the reason for transparency
                                    ai_context = self.ai_rationales.get(sym, "No AI context available")
                                    full_reason = f"{eval_data['reason']} | AI Context: {ai_context}"
                                    cursor.execute("""
                                        UPDATE paper_trades SET notes=? WHERE symbol=? AND entry_time=?
                                    """, (full_reason, sym, current_time.strftime('%Y-%m-%d %H:%M:%S')))
                                    
                                    trade_str_type = 'INTRADAY' if self.regimes.get(sym) == 'ORB' else 'DELIVERY'
                                    log_str = f"Entered {sym} {self.regimes.get(sym)} Breakout [{trade_str_type}] | Price: {exec_price:.2f} | Qty: {qty} | Slippage: {slippage_rate*100:.3f}%"
                                    if multiplier_used > 1.0:
                                        log_str += f" | (CONVICTION 1.5x)"
                                    log.info(log_str)
        
        conn.commit()
        conn.close()

    def run_live(self):
        log.info("Starting Live Paper Trader Daemon...")
        while True:
            now = datetime.now(ZoneInfo('Asia/Kolkata'))
            # Market hours: 09:15 to 15:30
            if now.hour == 9 and now.minute < 15:
                time.sleep(60)
                continue
            if now.hour >= 15 and now.minute > 30:
                time.sleep(60)
                continue
                
            # Process on the 5-minute marks (e.g. 09:20, 09:25)
            if now.minute % 5 == 0 and now.second < 10:
                log.info(f"--- Processing Tick: {now} ---")
                self.process_tick(now)
                time.sleep(10) # Prevent multiple executions in the same 5-minute mark
                
            time.sleep(1)

if __name__ == "__main__":
    trader = PaperTrader(YFinanceProvider(), is_live=True)
    trader.run_live()
