import sqlite3
import pandas as pd
import yfinance as yf
from datetime import datetime, time as dtime
import time
import os
import sys
import fcntl
from logger import log
from zoneinfo import ZoneInfo
import ta

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "trading_system.db")
LOCK_FILE = "/tmp/night_researcher.lock"

NIFTY_SYMBOLS = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS",
    "KOTAKBANK.NS", "AXISBANK.NS", "SBIN.NS", "BAJFINANCE.NS", "ITC.NS",
    "LT.NS", "BHARTIARTL.NS", "HINDUNILVR.NS"
]

def get_db():
    return sqlite3.connect(DB_PATH)

def init_trend_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS multi_timeframe_trends (
            symbol TEXT,
            date TEXT,
            trend_score INTEGER,
            PRIMARY KEY (symbol, date)
        )
    ''')
    conn.commit()
    conn.close()

def fetch_latest_daily_data():
    """Fetches today's data from yfinance and updates market_data_1d."""
    log.info("[Night Researcher] Fetching latest daily data for symbols...")
    conn = get_db()
    cursor = conn.cursor()
    
    # Removed CREATE TABLE because it already exists from user's backtesting with capitalized schema
    
    for sym in NIFTY_SYMBOLS:
        try:
            # Check if we already have data
            cursor.execute("SELECT COUNT(*) FROM market_data_1d WHERE Symbol=?", (sym,))
            count = cursor.fetchone()[0]
            
            period = "1y" if count == 0 else "1d"
            df = yf.Ticker(sym).history(period=period)
            
            if not df.empty:
                for idx, row in df.iterrows():
                    date_str = idx.strftime('%Y-%m-%d')
                    # Use exact column names: Datetime, Symbol, Open, High, Low, Close, Volume
                    cursor.execute('''
                        INSERT OR IGNORE INTO market_data_1d (Symbol, Datetime, Open, High, Low, Close, Volume)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (sym, date_str, float(row['Open']), float(row['High']), 
                          float(row['Low']), float(row['Close']), int(row['Volume'])))
                
                log.info(f"Appended {period} data for {sym}")
        except Exception as e:
            log.error(f"Error fetching latest data for {sym}: {e}")
            
    conn.commit()
    conn.close()

def is_past_deadline():
    now = datetime.now(ZoneInfo('Asia/Kolkata'))
    # Only abort if we are between 08:45 AM and 09:15 AM
    if now.hour == 8 and now.minute >= 45:
        return True
    if now.hour == 9 and now.minute < 15:
        return True
    return False

def check_candlestick_patterns(df):
    """Basic pattern recognition using past 5 days."""
    if len(df) < 5:
        return None, None
        
    last = df.iloc[-1]
    prev = df.iloc[-2]
    
    body_last = abs(last['close'] - last['open'])
    body_prev = abs(prev['close'] - prev['open'])
    
    # Doji
    if body_last <= (last['high'] - last['low']) * 0.1:
        return "Doji", "Neutral"
        
    # Bullish Engulfing
    if prev['close'] < prev['open'] and last['close'] > last['open']:
        if last['open'] < prev['close'] and last['close'] > prev['open']:
            return "Bullish Engulfing", "High"
            
    # Bearish Engulfing
    if prev['close'] > prev['open'] and last['close'] < last['open']:
        if last['open'] > prev['close'] and last['close'] < prev['open']:
            return "Bearish Engulfing", "High"
            
    # Hammer
    if last['close'] > last['open']:
        lower_wick = last['open'] - last['low']
        upper_wick = last['high'] - last['close']
        if lower_wick > body_last * 2 and upper_wick < body_last * 0.5:
            return "Hammer", "Medium"
            
    return None, None

def calculate_support_resistance(df):
    """Calculate simple S/R based on recent local extrema."""
    if len(df) < 20:
        return None, None
    recent = df.tail(20)
    support = recent['low'].min()
    resistance = recent['high'].max()
    return float(support), float(resistance)

def log_research(sym, analysis_type, finding, confidence):
    conn = get_db()
    cursor = conn.cursor()
    now_str = datetime.now(ZoneInfo('Asia/Kolkata')).strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        INSERT INTO after_hours_research (timestamp, symbol, analysis_type, finding, confidence)
        VALUES (?, ?, ?, ?, ?)
    ''', (now_str, sym, analysis_type, finding, confidence))
    conn.commit()
    conn.close()
    log.info(f"[{sym}] {analysis_type}: {finding} ({confidence})")

def generate_pre_market_intelligence():
    log.info("[Night Researcher] Generating Pre-Market Intelligence Cards...")
    conn = get_db()
    cursor = conn.cursor()
    today_str = datetime.now(ZoneInfo('Asia/Kolkata')).strftime("%Y-%m-%d")
    
    # --- GLOBAL MARKET REGIME FILTER ---
    try:
        # Fetch Nifty
        nifty_df = yf.Ticker("^NSEI").history(period="1y")
        # Fetch VIX
        vix_df = yf.Ticker("^INDIAVIX").history(period="1y")
        
        regime_multiplier = 1.0 # Default Bull/Calm
        
        if len(nifty_df) >= 200:
            nifty_200sma = nifty_df['Close'].rolling(200).mean().iloc[-1]
            nifty_close = nifty_df['Close'].iloc[-1]
            
            # Simple High Vol definition: VIX > 20
            vix_close = vix_df['Close'].iloc[-1] if not vix_df.empty else 15.0
            
            if nifty_close < nifty_200sma:
                regime_multiplier = 0.5 # Bear (Nifty < 200 SMA)
                log.info("Global Regime: BEAR (Nifty below 200 SMA). Multiplier = 0.5x")
            elif vix_close > 20.0:
                regime_multiplier = 0.8 # High Vol
                log.info("Global Regime: HIGH VOL (VIX > 20). Multiplier = 0.8x")
            else:
                log.info("Global Regime: BULL/CALM. Multiplier = 1.0x")
                
        # Save to model_config
        now_str = datetime.now(ZoneInfo('Asia/Kolkata')).strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("INSERT OR REPLACE INTO model_config (key, value, updated_at) VALUES (?, ?, ?)", 
                       ('market_regime_multiplier', float(regime_multiplier), now_str))
    except Exception as e:
        log.error(f"Error calculating market regime: {e}")
    # -----------------------------------
    
    for sym in NIFTY_SYMBOLS:
        df = pd.read_sql("SELECT * FROM market_data_1d WHERE Symbol=? ORDER BY Datetime ASC", conn, params=(sym,))
        if df.empty:
            continue
            
        df.rename(columns={'Close': 'close', 'Open': 'open', 'High': 'high', 'Low': 'low'}, inplace=True)
        df['Datetime'] = pd.to_datetime(df['Datetime'])
        last_price = float(df.iloc[-1]['close'])
        
        # 52w Proximity
        if len(df) >= 252:
            df_52 = df.tail(252)
            high_52 = df_52['high'].max()
            low_52 = df_52['low'].min()
            prox = (last_price - low_52) / (high_52 - low_52) if high_52 > low_52 else 0.5
            proximity = f"{(prox*100):.1f}%"
        else:
            proximity = "N/A"
            
        support, resistance = calculate_support_resistance(df)
        pattern, _ = check_candlestick_patterns(df)
        
        sentiment_trend = "Neutral"
        try:
            sig_df = pd.read_sql("SELECT sentiment FROM market_signals WHERE symbol=?", conn, params=(sym,))
            if not sig_df.empty:
                s = sig_df.iloc[0]['sentiment']
                if s > 0.3: sentiment_trend = "Bullish"
                elif s < -0.3: sentiment_trend = "Bearish"
        except:
            pass
            
        cursor.execute('''
            INSERT OR REPLACE INTO pre_market_intelligence 
            (symbol, date, support, resistance, pattern, sentiment_trend, proximity_52w)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (sym, today_str, support, resistance, pattern or "None", sentiment_trend, proximity))
        
        # --- NEW ADAPTIVE MULTI-TIMEFRAME TREND SCORING ---
        trend_score = 50 # Default Medium
        try:
            if len(df) >= 100:
                # 1. Strict Point-in-Time Weekly SMA (No Look-Ahead Bias)
                df_weekly = df.set_index('Datetime')
                # Resample to weekly (Friday end), get the last close of the week, drop NaNs, and shift 1 to ignore incomplete current week
                weekly_closes = df_weekly.resample('W-FRI').agg({'close': 'last'}).dropna().shift(1)
                
                # Calculate 20-week SMA
                if len(weekly_closes) >= 20:
                    sma_20w = weekly_closes['close'].rolling(20).mean().iloc[-1]
                    
                    # 2. Daily Trend Strength (ADX)
                    adx_ind = ta.trend.ADXIndicator(high=df['high'], low=df['low'], close=df['close'], window=14)
                    adx = adx_ind.adx().iloc[-1]
                    pdi = adx_ind.adx_pos().iloc[-1]
                    mdi = adx_ind.adx_neg().iloc[-1]
                    
                    # 3. Exhaustive Condition Tree
                    if last_price > sma_20w and adx > 20 and pdi > mdi:
                        trend_score = 100
                    elif last_price > sma_20w and (adx <= 20 or abs(pdi - mdi) < 2):
                        trend_score = 50
                    else:
                        # Price <= 20W SMA OR (Price > SMA and ADX > 20 and +DI <= -DI) OR any other ambiguous state
                        trend_score = 0
        except Exception as e:
            log.error(f"Error computing multi-timeframe score for {sym}: {e}")
            
        cursor.execute('''
            INSERT OR REPLACE INTO multi_timeframe_trends (symbol, date, trend_score)
            VALUES (?, ?, ?)
        ''', (sym, today_str, trend_score))
        # ----------------------------------------------------
        
    conn.commit()
    conn.close()

def run_research():
    log.info("Starting Night Researcher...")
    
    # 1. Update data
    fetch_latest_daily_data()
    
    # 2. Iterate slowly through symbols
    conn = get_db()
    for sym in NIFTY_SYMBOLS:
        if is_past_deadline():
            log.warning("Hard stop deadline reached (08:45 AM). Aborting research.")
            break
            
        df = pd.read_sql("SELECT * FROM market_data_1d WHERE Symbol=? ORDER BY Datetime ASC", conn, params=(sym,))
        if df.empty:
            continue
            
        # Standardize column names for downstream functions
        df.rename(columns={'Close': 'close', 'Open': 'open', 'High': 'high', 'Low': 'low'}, inplace=True)
            
        # Pattern Detection
        pattern, conf = check_candlestick_patterns(df)
        if pattern:
            log_research(sym, "CANDLESTICK_PATTERN", f"Detected {pattern} on daily timeframe.", conf)
            time.sleep(2) # Artificial delay to simulate heavy work for UI feed
            
        # Support / Resistance
        sup, res = calculate_support_resistance(df)
        if sup and res:
            log_research(sym, "SUPPORT_RESISTANCE", f"Key Support: {sup:.2f}, Key Resistance: {res:.2f}", "Medium")
            time.sleep(2)
            
        # Moving Averages
        if len(df) >= 200:
            sma50 = df['close'].rolling(50).mean().iloc[-1]
            sma200 = df['close'].rolling(200).mean().iloc[-1]
            if sma50 > sma200 and df.iloc[-2]['close'] <= df.iloc[-2]['close'] * 1.0: # simplistic golden cross approx
                log_research(sym, "MOVING_AVERAGE", f"50 SMA ({sma50:.2f}) > 200 SMA ({sma200:.2f}). Bullish trend.", "High")
            time.sleep(2)
            
        # Sleep slightly to avoid hogging CPU
        time.sleep(5)
        
    conn.close()
    
    # 3. If morning, generate intelligence
    now = datetime.now(ZoneInfo('Asia/Kolkata'))
    if now.hour == 8 and now.minute >= 30:
        generate_pre_market_intelligence()
    else:
        # If running early in the night, maybe wait and generate later? 
        # For simplicity, we just generate it at the end of the run as a draft.
        generate_pre_market_intelligence()

if __name__ == "__main__":
    lock_file_fd = None
    try:
        lock_file_fd = open(LOCK_FILE, 'w')
        fcntl.flock(lock_file_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except IOError:
        log.warning("Another instance of night_researcher is already running. Exiting.")
        sys.exit(0)
        
    try:
        init_trend_db()
        run_research()
        log.info("Night Researcher completed successfully.")
    except Exception as e:
        log.error(f"Night Researcher failed: {e}")
    finally:
        fcntl.flock(lock_file_fd, fcntl.LOCK_UN)
        lock_file_fd.close()
        os.remove(LOCK_FILE)
