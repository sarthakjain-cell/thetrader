import sqlite3

def patch_db():
    conn = sqlite3.connect("trading_system.db")
    cursor = conn.cursor()
    
    try:
        cursor.execute("ALTER TABLE scraped_news ADD COLUMN affected_sector TEXT")
    except sqlite3.OperationalError:
        pass # Column exists
        
    try:
        cursor.execute("ALTER TABLE scraped_news ADD COLUMN action_signal TEXT")
    except sqlite3.OperationalError:
        pass
        
    try:
        cursor.execute("ALTER TABLE scraped_news ADD COLUMN confidence_score REAL")
    except sqlite3.OperationalError:
        pass
        
    conn.commit()
    conn.close()
    print("Database patched successfully for Epic 15!")

if __name__ == "__main__":
    patch_db()
