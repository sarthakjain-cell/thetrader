import sqlite3
import hashlib
from datetime import datetime
from engine_b_advisor import aggregate_hourly_sentiment, rank_daily_tips, _get_db
from init_paper_db import init_paper_db
from logger import log
import pandas as pd

def inject_mock_headlines(target_date):
    conn = _get_db()
    cursor = conn.cursor()
    
    # Wipe Engine B tables
    cursor.execute("DELETE FROM raw_news")
    cursor.execute("DELETE FROM sentiment_scores")
    cursor.execute("DELETE FROM research_tips")
    
    headlines = [
        # Very Positive for RELIANCE (using extreme VADER words)
        (f"{target_date} 09:30:00", "Reliance is fantastic, wonderful, amazing, and excellent! Huge success!", "RELIANCE.NS"),
        (f"{target_date} 10:15:00", "Reliance secures massive global contract, brilliant market dominance, outstanding!", "RELIANCE.NS"),
        (f"{target_date} 11:00:00", "Reliance launches superb game-changing telecom service, phenomenal growth", "RELIANCE.NS"),
        
        # Mixed for TCS (More headlines, lower sentiment)
        (f"{target_date} 09:45:00", "TCS announces steady quarterly growth, meets expectations", "TCS.NS"),
        (f"{target_date} 10:30:00", "TCS wins minor contract in Europe", "TCS.NS"),
        (f"{target_date} 11:30:00", "TCS faces slight margin pressure due to wage hikes", "TCS.NS"),
        (f"{target_date} 13:00:00", "TCS expands partnership with AWS", "TCS.NS"),
        (f"{target_date} 14:00:00", "TCS management confident on long-term outlook", "TCS.NS"),
        
        # Very Negative for INFY
        (f"{target_date} 10:00:00", "Infosys cuts revenue guidance, shares plummet", "INFY.NS"),
        (f"{target_date} 14:30:00", "Infosys faces severe margin decline amidst macro headwinds", "INFY.NS")
    ]
    
    for ts, title, syms in headlines:
        h = hashlib.md5((title + str(ts)).encode('utf-8')).hexdigest()
        cursor.execute("""
            INSERT INTO raw_news (timestamp, source, title, link, hash, symbols_mentioned)
            VALUES (?, 'MockNews', ?, 'http://mock.com', ?, ?)
        """, (ts, title, h, syms))
        
    conn.commit()
    conn.close()
    log.info(f"Injected {len(headlines)} mock headlines for {target_date}.")

def verify_engine_b():
    target_date = "2026-07-15"
    inject_mock_headlines(target_date)
    
    # Simulate hourly aggregations
    hours = [9, 10, 11, 13, 14]
    for h in hours:
        # Mock time: e.g., 2026-07-15 09:59:59
        mock_time = datetime.strptime(f"{target_date} {h:02d}:59:59", '%Y-%m-%d %H:%M:%S')
        aggregate_hourly_sentiment(mock_time)
        
    # Simulate 16:00 Ranking
    mock_rank_time = datetime.strptime(f"{target_date} 16:00:00", '%Y-%m-%d %H:%M:%S')
    rank_daily_tips(mock_rank_time)
    
    # Read Tips
    conn = _get_db()
    tips = pd.read_sql("SELECT * FROM research_tips", conn)
    conn.close()
    
    log.info("\n--- Engine B Verification Results ---")
    if tips.empty:
        log.warning("No tips generated!")
    else:
        print(tips[['symbol', 'score', 'confidence', 'rationale']])
        
    # Validations
    if not tips.empty:
        assert tips.iloc[0]['symbol'] == 'RELIANCE.NS', "Reliance should be rank 1 due to extreme positive sentiment"
        assert tips.iloc[1]['symbol'] == 'TCS.NS', "TCS should be rank 2 due to moderate sentiment + high volume"
        assert 'INFY.NS' not in tips['symbol'].values, "INFY should not be recommended due to negative sentiment"
        log.info("✅ All Engine B Verification checks passed!")

if __name__ == "__main__":
    verify_engine_b()
