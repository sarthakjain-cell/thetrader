import sqlite3
import pandas as pd
from datetime import datetime
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from logger import log

DB_PATH = "trading_system.db"
# Initialize the NLP Brain
analyzer = SentimentIntensityAnalyzer()

def analyze_sentiment(text):
    """
    Uses NLP to score the sentiment of the text.
    Returns a compound score between -1 (Highly Negative) and 1 (Highly Positive).
    """
    scores = analyzer.polarity_scores(text)
    compound = scores['compound']
    
    if compound >= 0.05:
        label = "POSITIVE"
    elif compound <= -0.05:
        label = "NEGATIVE"
    else:
        label = "NEUTRAL"
        
    return compound, label

def process_new_articles():
    """The brain loop: Reads newly scraped articles and scores them."""
    log.info("Baby 2 is waking up... Scanning database for new scraped news...")
    
    conn = sqlite3.connect(DB_PATH)
    # Fetch articles that haven't been scored yet (the ones your scraper just added)
    df = pd.read_sql("SELECT * FROM scraped_news WHERE sentiment_score IS NULL", conn)
    
    if df.empty:
        log.info("No new articles to read right now.")
        conn.close()
        return
        
    log.info(f"Found {len(df)} new articles. Engaging NLP processors...")
    
    updates = []
    for index, row in df.iterrows():
        # The AI reads the headline and the content together
        text_to_analyze = f"{row['headline']}. {row['content']}"
        score, label = analyze_sentiment(text_to_analyze)
        
        updates.append((score, label, row['id']))
        log.info(f"Analyzed Article ID {row['id']} [{row['source']}]: Label=[{label}], Score=[{score}]")
        log.info(f" -> Related Ticker: {row['related_tickers']}")
        
    cursor = conn.cursor()
    # Save the AI's thoughts back into the database
    cursor.executemany("UPDATE scraped_news SET sentiment_score = ?, sentiment_label = ? WHERE id = ?", updates)
    conn.commit()
    conn.close()
    log.info("Successfully updated the database with Macro Sentiment Scores.")

if __name__ == "__main__":
    process_new_articles()
