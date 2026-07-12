import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "trading_system.db")

def apply_indexes():
    print("Applying Composite SQLite Indexes...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    queries = [
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_market_data_sym_date ON market_data_1d(Symbol, Datetime);",
        "CREATE INDEX IF NOT EXISTS idx_global_macro_date ON global_macro_features(date);",
        "CREATE INDEX IF NOT EXISTS idx_corporate_events_sym_date ON corporate_events(symbol, date);"
    ]
    
    for q in queries:
        try:
            cursor.execute(q)
            print(f"Executed: {q}")
        except Exception as e:
            print(f"Error executing {q}: {e}")
            
    conn.commit()
    conn.close()
    print("Indexes applied successfully.")

if __name__ == "__main__":
    apply_indexes()
