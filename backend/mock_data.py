import sqlite3
from datetime import datetime
import json

import yfinance as yf

def get_last_price(symbol):
    try:
        tkr = yf.Ticker(symbol)
        df = tkr.history(period="1d")
        if not df.empty:
            return float(df['Close'].iloc[-1])
    except Exception:
        pass
    return 100.0

def insert_mock_data():
    conn = sqlite3.connect('trading_system.db')
    c = conn.cursor()
    
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    today = datetime.now().strftime("%Y-%m-%d")
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS market_signals (
            symbol TEXT PRIMARY KEY,
            last_price REAL,
            regime TEXT,
            signal TEXT,
            rsi REAL,
            volume_spike REAL,
            adx REAL,
            sentiment REAL,
            confidence TEXT,
            updated_at TEXT
        )
    ''')
    
    # Try adding the notes column to paper_trades if it doesn't exist
    try:
        c.execute('ALTER TABLE paper_trades ADD COLUMN notes TEXT')
    except sqlite3.OperationalError:
        pass # Column might already exist
    
    # 1. Insert mock market signals so the scanner grid is populated
    mock_signals = [
        ('RELIANCE.NS', get_last_price('RELIANCE.NS'), 'BULLISH', 'HOLD', 65.2, 1.2, 28.5, 0.45, 'High', now_str),
        ('TCS.NS', get_last_price('TCS.NS'), 'BULLISH', 'BUY', 72.1, 2.5, 35.2, 0.82, 'High', now_str),
        ('HDFCBANK.NS', get_last_price('HDFCBANK.NS'), 'BEARISH', 'VETO', 45.0, 1.8, 22.1, -0.65, 'Medium', now_str),
        ('INFY.NS', get_last_price('INFY.NS'), 'CHOPPY', 'HOLD', 55.4, 0.9, 15.0, 0.12, 'Low', now_str),
        ('ICICIBANK.NS', get_last_price('ICICIBANK.NS'), 'BULLISH', 'BUY', 68.9, 3.1, 31.0, 0.55, 'High', now_str)
    ]
    
    for sig in mock_signals:
        c.execute('''
            INSERT INTO market_signals 
            (symbol, last_price, regime, signal, rsi, volume_spike, adx, sentiment, confidence, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(symbol) DO UPDATE SET
            last_price=excluded.last_price,
            regime=excluded.regime,
            signal=excluded.signal,
            rsi=excluded.rsi,
            volume_spike=excluded.volume_spike,
            adx=excluded.adx,
            sentiment=excluded.sentiment,
            confidence=excluded.confidence,
            updated_at=excluded.updated_at
        ''', sig)
        
    tcs_price = get_last_price('TCS.NS')
    
    # 2. Insert a mock trade for today so it appears on the chart and table
    notes_json = json.dumps({
        "time": now_str,
        "price": tcs_price,
        "sentiment": 0.82,
        "rsi": 71.5,
        "volume_spike": 2.2,
        "reason": "ORB Breakout confirmed. Sentiment is highly positive (+0.82) due to Q1 results."
    })
    
    # Clear the old mock trade
    c.execute("DELETE FROM paper_trades WHERE symbol='TCS.NS' AND reason='trailing_stop'")
    
    c.execute('''
        INSERT INTO paper_trades 
        (symbol, qty, entry_price, entry_time, exit_price, exit_time, pnl, reason, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        'TCS.NS', 10, tcs_price - 20, f"{today} 10:15:00", tcs_price + 20, f"{today} 14:30:00", 400.00, 'trailing_stop', notes_json
    ))
    
    conn.commit()
    conn.close()
    print("Mock data inserted successfully!")

if __name__ == '__main__':
    insert_mock_data()
