import sqlite3
from logger import log

DB_PATH = "trading_system.db"

def init_paper_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Paper Account State
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS paper_account (
            id INTEGER PRIMARY KEY,
            equity REAL NOT NULL,
            peak_equity REAL NOT NULL,
            is_halted BOOLEAN NOT NULL DEFAULT 0
        )
    ''')
    
    # 8. Intraday 5m Bars (Engine A Charting)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS intraday_5m (
        symbol TEXT,
        datetime TEXT,
        open REAL,
        high REAL,
        low REAL,
        close REAL,
        volume INTEGER,
        PRIMARY KEY (symbol, datetime)
    )
    ''')

    # 7. Macro Alerts (Engine B logic layer)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS macro_alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        theme_name TEXT,
        trigger_matched TEXT,
        positive_stocks TEXT,
        negative_stocks TEXT,
        confidence REAL,
        expiry_date TEXT
    )
    ''')

    # Initialize account if empty
    cursor.execute("SELECT COUNT(*) FROM paper_account")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO paper_account (id, equity, peak_equity, is_halted) VALUES (1, 100000.0, 100000.0, 0)")
        
    # 2. Open Positions
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS paper_positions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            entry_time TEXT NOT NULL,
            entry_price REAL NOT NULL,
            qty INTEGER NOT NULL,
            stop_loss REAL NOT NULL,
            target REAL NOT NULL
        )
    ''')
    
    # 3. Trade Ledger
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS paper_trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            entry_time TEXT NOT NULL,
            exit_time TEXT NOT NULL,
            entry_price REAL NOT NULL,
            exit_price REAL NOT NULL,
            qty INTEGER NOT NULL,
            pnl REAL NOT NULL,
            reason TEXT NOT NULL
        )
    ''')
    
    # 4. Daily Summary
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS daily_summary (
            date TEXT PRIMARY KEY,
            end_equity REAL NOT NULL,
            daily_pnl REAL NOT NULL,
            trades_count INTEGER NOT NULL,
            peak_drawdown REAL NOT NULL
        )
    ''')
    
    # Engine B: News Sentiment Advisor
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS raw_news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            source TEXT NOT NULL,
            title TEXT NOT NULL,
            link TEXT NOT NULL,
            hash TEXT UNIQUE NOT NULL,
            symbols_mentioned TEXT NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sentiment_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            hour INTEGER NOT NULL,
            symbol TEXT NOT NULL,
            avg_compound REAL NOT NULL,
            headline_count INTEGER NOT NULL,
            UNIQUE(date, hour, symbol)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS research_tips (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            symbol TEXT NOT NULL,
            score REAL NOT NULL,
            rationale TEXT NOT NULL,
            confidence TEXT NOT NULL,
            UNIQUE(date, symbol)
        )
    ''')
    
    conn.commit()
    conn.close()
    log.info("Paper trading and Engine B tables initialized successfully.")

if __name__ == "__main__":
    init_paper_db()
