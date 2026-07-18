import sqlite3
import feedparser
import time
import hashlib
import re
import json
import pandas as pd
from datetime import datetime, timedelta, time as dtime
from zoneinfo import ZoneInfo
import os
import google.generativeai as genai
from logger import log

DB_PATH = "trading_system.db"

# Initialize Gemini Client (Make sure GEMINI_API_KEY is in .env or exported)
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

FEEDS = [
    "https://economictimes.indiatimes.com/markets/rssfeeds/2146842.cms",
    "https://www.moneycontrol.com/rss/latestnews.xml",
    "https://www.livemint.com/rss/markets",
    "https://www.cnbctv18.com/rss/business.xml",
    "https://www.business-standard.com/rss/markets-106.rss",
    "https://feeds.feedburner.com/ndtvprofit-latest"
]

NIFTY_MAPPING = {
    "RELIANCE.NS": ["Reliance", "RIL", "Reliance Industries"],
    "TCS.NS": ["TCS", "Tata Consultancy"],
    "HDFCBANK.NS": ["HDFC", "HDFC Bank", "HDFC Ltd"],
    "INFY.NS": ["Infosys", "INFY"],
    "ICICIBANK.NS": ["ICICI", "ICICI Bank"],
    "KOTAKBANK.NS": ["Kotak", "Kotak Bank", "Kotak Mahindra"],
    "AXISBANK.NS": ["Axis", "Axis Bank"],
    "SBIN.NS": ["SBI", "State Bank", "SBIN"],
    "BAJFINANCE.NS": ["Bajaj Finance"],
    "ITC.NS": ["ITC"], 
    "LT.NS": ["L&T", "Larsen", "Larsen & Toubro"],
    "BHARTIARTL.NS": ["Bharti", "Airtel", "Bharti Airtel"],
    "HINDUNILVR.NS": ["HUL", "Hindustan Unilever"]
}
UNAMBIGUOUS_TICKERS = ["INFY", "TCS", "WIPRO", "HCLTECH", "SBIN"]

def _get_db():
    return sqlite3.connect(DB_PATH)

def map_symbols(title):
    matched_symbols = set()
    text = title.lower()
    
    for sym, aliases in NIFTY_MAPPING.items():
        for alias in aliases:
            if sym == "ITC.NS":
                # Special context check for ITC
                if re.search(r'\bitc\b\s*(ltd|share|stock|q\d)?', text, re.IGNORECASE):
                    matched_symbols.add(sym)
            else:
                # Basic word boundary match for alias
                pattern = r'\b' + re.escape(alias.lower()) + r'\b'
                if re.search(pattern, text):
                    matched_symbols.add(sym)
                    
    # Exact ticker match fallback
    for ticker in UNAMBIGUOUS_TICKERS:
        pattern = r'\b' + re.escape(ticker.lower()) + r'\b'
        if re.search(pattern, text):
            # Find the .NS symbol
            ns_sym = ticker + ".NS"
            if ns_sym in NIFTY_MAPPING:
                matched_symbols.add(ns_sym)
                
    return list(matched_symbols)

def scrape_feeds():
    log.info("Starting RSS Scrape...")
    conn = _get_db()
    cursor = conn.cursor()
    
    # Load Macro Matrix
    try:
        with open("macro_matrix.json", "r") as f:
            macro_config = json.load(f)
            macro_themes = macro_config.get("macro_themes", [])
    except Exception as e:
        log.error(f"Failed to load macro_matrix.json: {e}")
        macro_themes = []
        
    new_headlines = 0
    macro_alerts_triggered = 0
    current_time = datetime.now(ZoneInfo('Asia/Kolkata'))
    current_time_str = current_time.strftime('%Y-%m-%d %H:%M:%S')
    expiry_date_str = (current_time + timedelta(days=3)).strftime('%Y-%m-%d')
    
    for feed_url in FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries:
                title = entry.title
                link = entry.link
                
                # Hash for deduplication
                hash_str = hashlib.md5((title + link).encode('utf-8')).hexdigest()
                
                cursor.execute("SELECT id FROM raw_news WHERE hash=?", (hash_str,))
                if cursor.fetchone() is not None:
                    continue # duplicate
                    
                symbols = map_symbols(title)
                
                # Check for Macro Event Triggers (even if no specific symbol is mentioned)
                title_lower = title.lower()
                for theme in macro_themes:
                    for trigger in theme.get('triggers', []):
                        if trigger.lower() in title_lower:
                            # Macro triggered! Check if already alerted recently
                            cursor.execute("SELECT id FROM macro_alerts WHERE theme_name=? AND expiry_date >= ?", (theme['name'], current_time.strftime('%Y-%m-%d')))
                            if cursor.fetchone() is None:
                                cursor.execute("""
                                    INSERT INTO macro_alerts (date, theme_name, trigger_matched, positive_stocks, negative_stocks, confidence, expiry_date)
                                    VALUES (?, ?, ?, ?, ?, ?, ?)
                                """, (
                                    current_time.strftime('%Y-%m-%d'),
                                    theme['name'],
                                    trigger,
                                    ",".join(theme.get('positive_stocks', [])),
                                    ",".join(theme.get('negative_stocks', [])),
                                    theme.get('confidence', 0.8),
                                    expiry_date_str
                                ))
                                macro_alerts_triggered += 1
                                log.warning(f"MACRO ALERT TRIGGERED: {theme['name']} via '{trigger}'")
                            break # Found a trigger for this theme, stop checking other triggers for this theme
                
                if not symbols: continue # skip standard sentiment if no exact symbols
                
                cursor.execute("""
                    INSERT INTO raw_news (timestamp, source, title, link, hash, symbols_mentioned)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (current_time_str, feed_url, title, link, hash_str, ",".join(symbols)))
                new_headlines += 1
                
        except Exception as e:
            log.error(f"Error scraping {feed_url}: {e}")
            
        time.sleep(2) # polite delay
        
    conn.commit()
    conn.close()
    log.info(f"Scrape Complete. Added {new_headlines} relevant headlines. Triggered {macro_alerts_triggered} macro alerts.")
    
def aggregate_hourly_sentiment(current_time=None):
    log.info("Aggregating hourly sentiment...")
    conn = _get_db()
    
    now = current_time or datetime.now(ZoneInfo('Asia/Kolkata'))
    current_date = now.strftime('%Y-%m-%d')
    current_hour = now.hour
    
    start_time = now.replace(minute=0, second=0, microsecond=0).strftime('%Y-%m-%d %H:%M:%S')
    end_time = now.strftime('%Y-%m-%d %H:%M:%S')
    
    # We now fetch enriched news from scraped_news instead of raw_news to use the LLM score
    df = pd.read_sql(f"SELECT * FROM scraped_news WHERE timestamp >= '{start_time}' AND timestamp <= '{end_time}'", conn)
    
    if df.empty:
        conn.close()
        return
        
    scores = []
    for _, row in df.iterrows():
        # Convert action_signal to a float score
        signal = row.get('action_signal', '')
        conf = float(row.get('confidence_score', 0.0) or 0.0)
        
        if "BUY" in signal:
            score = conf
        elif "SELL" in signal:
            score = -conf
        else:
            score = 0.0
            
        symbols = (row.get('related_tickers') or '').split(',')
        for sym in symbols:
            if sym.strip() and sym.strip() != "GENERAL_MARKET":
                scores.append({'symbol': sym.strip(), 'score': score})
            
    if not scores:
        conn.close()
        return
        
    scores_df = pd.DataFrame(scores)
    agg = scores_df.groupby('symbol').agg(
        avg_compound=('score', 'mean'),
        headline_count=('score', 'count')
    ).reset_index()
    
    cursor = conn.cursor()
    for _, row in agg.iterrows():
        cursor.execute("""
            INSERT OR REPLACE INTO sentiment_scores (date, hour, symbol, avg_compound, headline_count)
            VALUES (?, ?, ?, ?, ?)
        """, (current_date, current_hour, row['symbol'], row['avg_compound'], int(row['headline_count'])))
        
    conn.commit()
    conn.close()
    
def rank_daily_tips(current_time=None):
    log.info("Ranking daily tips...")
    conn = _get_db()
    
    now = current_time or datetime.now(ZoneInfo('Asia/Kolkata'))
    current_date = now.strftime('%Y-%m-%d')
    
    df = pd.read_sql(f"SELECT * FROM sentiment_scores WHERE date = '{current_date}'", conn)
    if df.empty:
        conn.close()
        log.warning("No sentiment scores found for today to rank.")
        return
        
    # Aggregate over all hours today
    agg = df.groupby('symbol').agg(
        total_compound=('avg_compound', 'mean'),
        total_count=('headline_count', 'sum')
    ).reset_index()
    
    max_count = agg['total_count'].max()
    if max_count == 0:
        conn.close()
        return
        
    agg['norm_count'] = agg['total_count'] / max_count
    agg['composite'] = 0.7 * agg['total_compound'] + 0.3 * agg['norm_count']
    
    # Top 3 positive
    top_3 = agg[agg['composite'] > 0].sort_values('composite', ascending=False).head(3)
    
    cursor = conn.cursor()
    cursor.execute("DELETE FROM research_tips WHERE date = ?", (current_date,))
    
    # We need the most positive headline rationale
    raw_df = pd.read_sql(f"SELECT * FROM scraped_news WHERE timestamp LIKE '{current_date}%'", conn)
    
    for _, row in top_3.iterrows():
        sym = row['symbol']
        score = row['composite']
        
        # Get most positive headline
        best_title = "No rationale available."
        best_score = -1
        
        for _, raw in raw_df.iterrows():
            tickers = raw.get('related_tickers', '')
            if sym in tickers:
                signal = raw.get('action_signal', '')
                conf = float(raw.get('confidence_score', 0.0) or 0.0)
                
                if "BUY" in signal:
                    comp = conf
                elif "SELL" in signal:
                    comp = -conf
                else:
                    comp = 0.0
                    
                if comp > best_score:
                    best_score = comp
                    best_title = raw['headline']
                    
        rationale = f"{best_title} (Sentiment: {score:+.2f})"
        
        confidence = "Low"
        if score > 0.5: confidence = "High"
        elif score >= 0.2: confidence = "Medium"
        
        cursor.execute("""
            INSERT INTO research_tips (date, symbol, score, rationale, confidence)
            VALUES (?, ?, ?, ?, ?)
        """, (current_date, sym, score, rationale, confidence))
        
        log.info(f"Generated Tip: {sym} | Conf: {confidence} | Score: {score:.2f}")
        
    conn.commit()
    conn.close()

def analyze_with_llm(headline, content):
    if not os.getenv("GEMINI_API_KEY"):
        return "General Market", "⚪ HOLD", 0.5
        
    prompt = f"""
You are a ruthless, highly experienced Hedge Fund Quantitative Analyst. 
Your job is to read market news and determine if it represents a highly confident, actionable trading signal.

Headline: {headline}
Content: {content}

You must output a strictly formatted JSON object with the following fields:
1. "affected_sector": The sector this news impacts most (e.g., "IT & Tech", "Banking & Finance", "Pharma Sector", "Energy/Oil", "Auto Sector", "FMCG", "Metals & Mining", or "General Market").
2. "action_signal": Must be EXACTLY one of: "🟢 BUY", "🔴 SELL", or "⚪ HOLD". 
    - Output BUY or SELL ONLY if the news is a definitive, high-impact catalyst (e.g., major earnings beat, CEO resignation, massive contract won, severe regulatory action).
    - Output HOLD if the news is general market chatter, analyst opinions, routine updates, or if the impact is ambiguous.
3. "confidence_score": A float between 0.0 and 1.0 representing your confidence in the action_signal.
4. "rationale": A concise, 1-2 sentence explanation of your reasoning.
"""
    try:
        model = genai.GenerativeModel('gemini-1.5-pro')
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                temperature=0.1,
            )
        )
        
        res_json = json.loads(response.text)
        
        sector = res_json.get("affected_sector", "General Market")
        signal = res_json.get("action_signal", "⚪ HOLD")
        conf = float(res_json.get("confidence_score", 0.5))
        
        # Guardrails
        if signal not in ["🟢 BUY", "🔴 SELL", "⚪ HOLD"]:
            signal = "⚪ HOLD"
            
        return sector, signal, conf
    except Exception as e:
        log.error(f"LLM Analysis failed: {e}")
        return "General Market", "⚪ HOLD", 0.5

def enrich_scraped_news():
    log.info("Enriching newly scraped news with Gemini 1.5 Pro signals...")
    conn = _get_db()
    cursor = conn.cursor()
    
    try:
        # Fetch news that hasn't been enriched yet
        cursor.execute("SELECT id, headline, content FROM scraped_news WHERE action_signal IS NULL")
        rows = cursor.fetchall()
        
        for row in rows:
            news_id, headline, content = row
            
            # Use Gemini 1.5 Pro
            affected_sector, action_signal, confidence_score = analyze_with_llm(headline, content or "")
                
            cursor.execute('''
                UPDATE scraped_news 
                SET affected_sector=?, action_signal=?, confidence_score=? 
                WHERE id=?
            ''', (affected_sector, action_signal, confidence_score, news_id))
            
            # polite delay for API limits
            time.sleep(0.5)
            
        conn.commit()
        if len(rows) > 0:
            log.info(f"Successfully enriched {len(rows)} news articles via Gemini.")
    except Exception as e:
        log.error(f"Error enriching scraped news: {e}")
    finally:
        conn.close()

class EngineBAdvisor:
    def __init__(self):
        self.last_scrape_hour = -1
        self.has_ranked_today = False
        self.last_date = None

    def run_live(self):
        log.info("Starting Engine B Advisor Daemon...")
        
        # Force an initial scrape and rank on startup so the dashboard isn't empty
        log.info("Performing initial startup scrape & rank...")
        scrape_feeds()
        aggregate_hourly_sentiment()
        rank_daily_tips()
        
        while True:
            now = datetime.now(ZoneInfo('Asia/Kolkata'))
            current_date = now.date()
            
            if self.last_date != current_date:
                self.has_ranked_today = False
                self.last_date = current_date
            
            t = now.time()
            
            # Continuous fast enrichment loop for new news
            enrich_scraped_news()
            
            # Pre-market scrape at 08:45
            if t.hour == 8 and t.minute >= 45 and self.last_scrape_hour != 8:
                scrape_feeds()
                self.last_scrape_hour = 8
                
            # Hourly scrape 09:00 - 15:00
            if 9 <= t.hour <= 15:
                if t.minute >= 15 and self.last_scrape_hour != t.hour:
                    scrape_feeds()
                    aggregate_hourly_sentiment()
                    self.last_scrape_hour = t.hour
                    
            # Post-market scrape 15:30
            if t.hour == 15 and t.minute >= 30 and self.last_scrape_hour != 15.5:
                scrape_feeds()
                aggregate_hourly_sentiment()
                self.last_scrape_hour = 15.5
                
            # Ranking at 16:00
            if t.hour >= 16 and not self.has_ranked_today:
                rank_daily_tips()
                self.has_ranked_today = True
                
            time.sleep(60)

if __name__ == "__main__":
    advisor = EngineBAdvisor()
    advisor.run_live()
