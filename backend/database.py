import sqlite3
import os
from contextlib import contextmanager

DB_PATH = "trading_system.db"

def init_db():
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Trades Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                symbol TEXT NOT NULL,
                action TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                price REAL NOT NULL,
                status TEXT NOT NULL,
                notes TEXT
            )
        ''')
        
        # Signals Table (Historical specific events)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                symbol TEXT NOT NULL,
                signal_type TEXT NOT NULL,
                confidence REAL,
                price_at_signal REAL
            )
        ''')
        
        # Market Signals Table (Live Snapshot)
        cursor.execute('''
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
        
        # Account Snapshots
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                capital REAL NOT NULL,
                unrealized_pnl REAL NOT NULL,
                realized_pnl REAL NOT NULL
            )
        ''')
        
        # After Hours Research
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS after_hours_research (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                symbol TEXT NOT NULL,
                analysis_type TEXT NOT NULL,
                finding TEXT NOT NULL,
                confidence TEXT
            )
        ''')
        
        # Pre Market Intelligence
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pre_market_intelligence (
                symbol TEXT PRIMARY KEY,
                date TEXT NOT NULL,
                support REAL,
                resistance REAL,
                pattern TEXT,
                sentiment_trend TEXT,
                proximity_52w TEXT
            )
        ''')
        
        # AI Forecasts (Pre-calculated by model_trainer.py)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_ai_forecasts (
                symbol TEXT PRIMARY KEY,
                date TEXT NOT NULL,
                probability REAL,
                feature_contributions TEXT
            )
        ''')
        
        # Model Metrics (Drift detection and threshold)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS model_metrics (
                date TEXT PRIMARY KEY,
                train_period_end TEXT,
                test_accuracy_recent REAL,
                profit_factor_hypothetical REAL,
                feature_importances TEXT
            )
        ''')
        
        # Model Config (Dynamic threshold storage)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS model_config (
                key TEXT PRIMARY KEY,
                value REAL,
                updated_at TEXT
            )
        ''')
        
        conn.commit()

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully.")
