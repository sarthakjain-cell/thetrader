import sqlite3
import pandas as pd

DB_PATH = "trading_system.db"

def get_today_trades():
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql("SELECT * FROM paper_positions WHERE date(entry_time) = '2026-08-05'", conn)
        print("--- Trades Taken Today (2026-08-05) ---")
        if df.empty:
            print("No trades taken today.")
        else:
            print(df.to_string(index=False))
        conn.close()
    except Exception as e:
        print(f"Error querying DB: {e}")

if __name__ == "__main__":
    get_today_trades()
