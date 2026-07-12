import sqlite3
import os

DB_PATH = "trading_system.db"

def patch_db():
    print(f"Connecting to {DB_PATH}...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Alter paper_positions to add strategy_id
    try:
        cursor.execute("ALTER TABLE paper_positions ADD COLUMN strategy_id TEXT DEFAULT 'S001_ORB'")
        print("Added strategy_id to paper_positions.")
    except sqlite3.OperationalError as e:
        print(f"Skipping paper_positions: {e}")

    # Alter paper_trades to add strategy_id
    try:
        cursor.execute("ALTER TABLE paper_trades ADD COLUMN strategy_id TEXT DEFAULT 'S001_ORB'")
        print("Added strategy_id to paper_trades.")
    except sqlite3.OperationalError as e:
        print(f"Skipping paper_trades: {e}")

    # Create strategy_performance table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS strategy_performance (
        strategy_id TEXT PRIMARY KEY,
        name TEXT,
        description TEXT,
        is_active INTEGER DEFAULT 1,
        total_trades INTEGER DEFAULT 0,
        win_rate REAL DEFAULT 0.0,
        profit_factor REAL DEFAULT 0.0,
        net_pnl REAL DEFAULT 0.0,
        max_drawdown REAL DEFAULT 0.0
    )
    """)
    print("Created strategy_performance table.")
    
    # Insert ORB strategy
    cursor.execute("""
    INSERT OR IGNORE INTO strategy_performance (strategy_id, name, description)
    VALUES ('S001_ORB', 'AI Open Range Breakout', 'Trades ORB breakouts when supported by AI Macro conviction.')
    """)

    # Insert VWAP strategy
    cursor.execute("""
    INSERT OR IGNORE INTO strategy_performance (strategy_id, name, description)
    VALUES ('S002_VWAP', 'VWAP Mean Reversion', 'Trades bounces off the daily VWAP band.')
    """)
    
    conn.commit()
    conn.close()
    print("DB Patch Complete.")

if __name__ == "__main__":
    patch_db()
