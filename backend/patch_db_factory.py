import sqlite3

DB_PATH = "trading_system.db"

def patch_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Table to store dynamically generated strategies that passed validation
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS generated_strategies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            strategy_id TEXT UNIQUE NOT NULL,
            generation_date TEXT NOT NULL,
            profit_factor REAL NOT NULL,
            win_rate REAL NOT NULL,
            total_trades INTEGER NOT NULL,
            config_json TEXT NOT NULL
        )
    """)
    
    conn.commit()
    conn.close()
    print("Database patched for Strategy Factory.")

if __name__ == "__main__":
    patch_db()
