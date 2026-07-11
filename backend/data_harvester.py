import sqlite3
import yfinance as yf
from datetime import datetime
from zoneinfo import ZoneInfo
from logger import log
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "trading_system.db")

NIFTY_SYMBOLS = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS",
    "KOTAKBANK.NS", "AXISBANK.NS", "SBIN.NS", "BAJFINANCE.NS", "ITC.NS",
    "LT.NS", "BHARTIARTL.NS", "HINDUNILVR.NS"
]

def init_macro_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scraped_news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            source TEXT NOT NULL,
            headline TEXT NOT NULL,
            content TEXT,
            sentiment_score REAL,
            sentiment_label TEXT,
            related_tickers TEXT,
            UNIQUE(headline, related_tickers)
        )
    ''')
    conn.commit()
    conn.close()

def fetch_and_store_news():
    log.info("[Data Harvester] Starting daily macro data scrape from yfinance...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    total_added = 0
    now_str = datetime.now(ZoneInfo('Asia/Kolkata')).strftime("%Y-%m-%d %H:%M:%S")
    
    for sym in NIFTY_SYMBOLS:
        try:
            ticker = yf.Ticker(sym)
            news = ticker.news
            for article in news:
                title = article.get('title', '')
                publisher = article.get('publisher', 'Unknown')
                # yfinance provides summary or we use title
                content = article.get('summary', title) 
                
                if not title: continue
                
                # We use INSERT OR IGNORE with UNIQUE constraint to prevent duplicate news
                cursor.execute('''
                    INSERT OR IGNORE INTO scraped_news 
                    (timestamp, source, headline, content, related_tickers)
                    VALUES (?, ?, ?, ?, ?)
                ''', (now_str, publisher, title, content, sym))
                
                if cursor.rowcount > 0:
                    total_added += 1
        except Exception as e:
            log.error(f"[Data Harvester] Error fetching news for {sym}: {e}")
            
    conn.commit()
    conn.close()
    log.info(f"[Data Harvester] Scraped and stored {total_added} new distinct articles.")

if __name__ == "__main__":
    init_macro_db()
    fetch_and_store_news()
