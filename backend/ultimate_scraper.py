import sqlite3
import requests
from bs4 import BeautifulSoup
import yfinance as yf
from datetime import datetime
from zoneinfo import ZoneInfo
from logger import log
import os
import time
import random
import hashlib
import xml.etree.ElementTree as ET
import threading
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "trading_system.db")

class RateLimiter:
    def __init__(self, max_tokens, refill_time):
        self.max_tokens = max_tokens
        self.refill_time = refill_time
        self.tokens = max_tokens
        self.last_refill = time.time()
        self.lock = threading.Lock()
        
    def wait_and_consume(self):
        while True:
            with self.lock:
                now = time.time()
                elapsed = now - self.last_refill
                if elapsed >= self.refill_time:
                    self.tokens = self.max_tokens
                    self.last_refill = now
                
                if self.tokens > 0:
                    self.tokens -= 1
                    return
            time.sleep(0.5)

NIFTY_SYMBOLS = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS",
    "KOTAKBANK.NS", "AXISBANK.NS", "SBIN.NS", "BAJFINANCE.NS", "ITC.NS",
    "LT.NS", "BHARTIARTL.NS", "HINDUNILVR.NS"
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

SECTOR_MAPPING = {
    "Pharma Sector": ["pharma", "drug", "fda", "sun pharma", "cipla", "dr reddy", "lupin"],
    "Banking & Finance": ["bank", "rbi", "lender", "nbfc", "finance", "loan", "interest rate", "repo rate"],
    "IT & Tech": ["tech", "software", "it sector", "nasdaq", "silicon", "ai"],
    "Auto Sector": ["auto", "vehicle", "ev", "maruti", "tata motors", "mahindra"],
    "Metals & Mining": ["metal", "steel", "mining", "tata steel", "hindalco", "jsw"],
    "FMCG": ["fmcg", "consumer goods", "retail", "inflation"]
}

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0"
]

class UltimateScraper:
    def __init__(self):
        self.session = requests.Session()
        self.init_db()
        self.mc_limiter = RateLimiter(max_tokens=4, refill_time=60.0) # 4 per min
        self.yf_limiter = RateLimiter(max_tokens=1, refill_time=2.0)  # 1 per 2s

    def init_db(self):
        conn = sqlite3.connect(DB_PATH, timeout=10.0)
        cursor = conn.cursor()
        # Adding content_hash to ensure strict deduplication across sources
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scraped_news (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                source TEXT NOT NULL,
                headline TEXT NOT NULL,
                content TEXT,
                sentiment_score REAL,
                sentiment_label TEXT,
                related_tickers TEXT,
                content_hash TEXT UNIQUE
            )
        ''')
        # Ensure the unique constraint exists. If not, this is a soft migration path.
        try:
            cursor.execute('CREATE UNIQUE INDEX idx_content_hash ON scraped_news(content_hash)')
        except:
            pass
            
        # Phase 2: Corporate Events (Logging-Only Mode)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS corporate_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                symbol TEXT NOT NULL,
                event_type TEXT NOT NULL,
                event_value REAL,
                source TEXT NOT NULL,
                announce_date TEXT,
                ex_date TEXT,
                UNIQUE(date, symbol, event_type, source)
            )
        ''')
        conn.commit()
        conn.close()

    def safe_request(self, url, response_type='text'):
        """Anti-Block Arsenal: Rotates UAs, maintains session, random sleep."""
        headers = {
            'User-Agent': random.choice(USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://www.google.com/',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        # Polite delay to mimic human reading speed
        time.sleep(random.uniform(1.5, 4.0))
        
        try:
            response = self.session.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            if response_type == 'text':
                return response.text
            elif response_type == 'content':
                return response.content
        except Exception as e:
            log.error(f"[Scraper] Failed to fetch {url}: {e}")
            return None

    def insert_article(self, source, headline, content, related_tickers):
        """Hashes the content and inserts into DB if it doesn't already exist."""
        hash_input = f"{source}-{headline}-{related_tickers}".encode('utf-8')
        content_hash = hashlib.sha256(hash_input).hexdigest()
        
        conn = sqlite3.connect(DB_PATH, timeout=10.0)
        cursor = conn.cursor()
        now_str = datetime.now(ZoneInfo('Asia/Kolkata')).strftime("%Y-%m-%d %H:%M:%S")
        
        try:
            cursor.execute('''
                INSERT INTO scraped_news 
                (timestamp, source, headline, content, related_tickers, content_hash)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (now_str, source, headline, content, related_tickers, content_hash))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            # Duplicate found via UNIQUE constraint
            pass
        except Exception as e:
            log.error(f"[Scraper] Database error: {e}")
        finally:
            conn.close()
        return False
        
    def smart_extract_tags(self, title, content):
        """Extracts specific stocks or sectors from the headline/content using NLP keywords."""
        text = f"{title} {content}".lower()
        
        # 1. Check for specific Nifty stocks
        for sym, aliases in NIFTY_MAPPING.items():
            for alias in aliases:
                pattern = r'\b' + re.escape(alias.lower()) + r'\b'
                if re.search(pattern, text):
                    return sym # Return the exact stock ticker
                    
        # 2. Check for broader sectors
        for sector, keywords in SECTOR_MAPPING.items():
            for keyword in keywords:
                pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
                if re.search(pattern, text):
                    return sector # Return the sector string
                    
        # 3. Fallback to broad market
        return "GENERAL_MARKET"

    def scrape_rbi_rss(self):
        """Scrapes the official RBI Press Release RSS Feed."""
        log.info("[Scraper] Initiating RBI RSS Protocol...")
        url = "https://rbi.org.in/Scripts/BS_PressRelease.aspx?feed=rss"
        xml_data = self.safe_request(url)
        
        if not xml_data: return 0
        
        added = 0
        try:
            root = ET.fromstring(xml_data)
            for item in root.findall('.//item'):
                title = item.findtext('title')
                description = item.findtext('description')
                if title:
                    if self.insert_article('RBI', title, description or '', 'MACRO_INDIA'):
                        added += 1
        except Exception as e:
            log.error(f"[Scraper] RBI Parsing Error: {e}")
            
        return added

    def scrape_sebi_press_releases(self):
        """Scrapes SEBI's press release page using BeautifulSoup."""
        log.info("[Scraper] Initiating SEBI HTML Parsing Protocol...")
        url = "https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListingAll=yes&cid=16"
        html = self.safe_request(url)
        
        if not html: return 0
        
        added = 0
        try:
            soup = BeautifulSoup(html, 'html.parser')
            # SEBI typically uses table-based or list-based structures. 
            # We target the main content block containing links to PRs.
            links = soup.find_all('a', href=True)
            for link in links:
                href = link['href']
                title = link.get_text(strip=True)
                # Filter for typical PR structures
                if "PRNo" in href or len(title) > 40:
                    if "sebi.gov.in" not in href:
                        href = "https://www.sebi.gov.in" + href
                    if self.insert_article('SEBI', title, href, 'MACRO_INDIA'):
                        added += 1
                        
                # Limit to 10 latest to prevent scraping the entire historical archive
                if added >= 10: 
                    break
        except Exception as e:
            log.error(f"[Scraper] SEBI Parsing Error: {e}")
            
        return added

    def scrape_yfinance_news(self):
        """Aggregates Yahoo Finance news for the Nifty 50 watchlist."""
        log.info("[Scraper] Initiating YFinance Aggregator...")
        added = 0
        for sym in NIFTY_SYMBOLS:
            self.yf_limiter.wait_and_consume()
            try:
                ticker = yf.Ticker(sym)
                news = ticker.news
                if not news: continue
                
                for article in news:
                    title = article.get('title', '')
                    publisher = article.get('publisher', 'YFinance')
                    content = article.get('summary', title)
                    
                    if not title: continue
                    
                    if self.insert_article(publisher, title, content, sym):
                        added += 1
                        
            except Exception as e:
                log.error(f"[Scraper] YFinance Error for {sym}: {e}")
            
        log.info(f"-> Acquired {added} new Financial News headlines.")
        return added

    def scrape_yfinance_actions(self):
        """Phase 2: Safely log post-facto Dividends & Splits (ex-dates) with throttling."""
        log.info("[Scraper] Initiating YFinance Corporate Actions (Dividends/Splits)...")
        added = 0
        
        for sym in NIFTY_SYMBOLS:
            self.yf_limiter.wait_and_consume()
            try:
                ticker = yf.Ticker(sym)
                actions = ticker.actions
                if not actions.empty:
                    recent_actions = actions.tail(5)
                    for idx, row in recent_actions.iterrows():
                        ex_date_str = idx.strftime('%Y-%m-%d')
                        div = float(row['Dividends'])
                        split = float(row['Stock Splits'])
                        
                        conn = sqlite3.connect(DB_PATH)
                        cursor = conn.cursor()
                        
                        if div > 0:
                            try:
                                cursor.execute('''
                                    INSERT INTO corporate_events 
                                    (date, symbol, event_type, event_value, source, ex_date)
                                    VALUES (?, ?, ?, ?, ?, ?)
                                ''', (ex_date_str, sym, 'Dividend', div, 'yfinance', ex_date_str))
                                conn.commit()
                                added += 1
                            except sqlite3.IntegrityError:
                                pass
                        
                        if split > 0:
                            try:
                                cursor.execute('''
                                    INSERT INTO corporate_events 
                                    (date, symbol, event_type, event_value, source, ex_date)
                                    VALUES (?, ?, ?, ?, ?, ?)
                                ''', (ex_date_str, sym, 'Split', split, 'yfinance', ex_date_str))
                                conn.commit()
                                added += 1
                            except sqlite3.IntegrityError:
                                pass
                        conn.close()
            except Exception as e:
                log.error(f"[Scraper] YFinance Actions Error for {sym}: {e}")
                
        log.info(f"-> Logged {added} new corporate events from YFinance.")
        return added

    def scrape_et_markets_rss(self):
        """Scrapes the Economic Times Markets RSS feed for live general market news."""
        log.info("[Scraper] Initiating ET Markets RSS Protocol...")
        url = "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms"
        xml_data = self.safe_request(url)
        
        if not xml_data: return 0
        
        added = 0
        try:
            root = ET.fromstring(xml_data)
            for item in root.findall('.//item'):
                title = item.findtext('title')
                description = item.findtext('description')
                # Strip HTML tags from description if any
                if description:
                    description = BeautifulSoup(description, 'html.parser').get_text(strip=True)
                
                if title:
                    # Extract intelligent tags based on text analysis
                    full_desc = description or ''
                    smart_tag = self.smart_extract_tags(title, full_desc)
                    
                    if self.insert_article('Economic Times', title, full_desc, smart_tag):
                        added += 1
                        
                if added >= 50: # Cap at 50 per run
                    break
        except Exception as e:
            log.error(f"[Scraper] ET Markets Parsing Error: {e}")
            
        return added

    def scrape_moneycontrol_earnings(self):
        """Phase 2: Crash-protected earnings calendar scraper."""
        log.info("[Scraper] Initiating Moneycontrol Earnings Calendar...")
        url = "https://www.moneycontrol.com/stocks/marketinfo/board-meetings/homebody.php?type=1"
        added = 0
        self.mc_limiter.wait_and_consume()
        try:
            html = self.safe_request(url)
            if not html: return 0
            
            soup = BeautifulSoup(html, 'html.parser')
            table = soup.find('table', {'class': 'mctable1'})
            if not table:
                log.warning("[Scraper] Moneycontrol parsing warning: Could not find 'mctable1'. Falling back to empty set.")
                return 0
                
            rows = table.find_all('tr')
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 3:
                    company_name = cols[0].get_text(strip=True).upper()
                    board_date = cols[1].get_text(strip=True)
                    purpose = cols[2].get_text(strip=True)
                    
                    matched_sym = None
                    for sym in NIFTY_SYMBOLS:
                        base = sym.replace('.NS', '')
                        if base in company_name or company_name.startswith(base[:5]):
                            matched_sym = sym
                            break
                            
                    if matched_sym and ('Result' in purpose or 'Audited' in purpose):
                        try:
                            parsed_date = datetime.strptime(board_date, "%d-%b-%y").strftime("%Y-%m-%d")
                        except:
                            parsed_date = board_date
                            
                        conn = sqlite3.connect(DB_PATH)
                        cursor = conn.cursor()
                        try:
                            # Log as 'Earnings' with the board_meeting_date as announce_date
                            cursor.execute('''
                                INSERT INTO corporate_events 
                                (date, symbol, event_type, event_value, source, announce_date)
                                VALUES (?, ?, ?, ?, ?, ?)
                            ''', (parsed_date, matched_sym, 'Earnings', 0, 'moneycontrol', parsed_date))
                            conn.commit()
                            added += 1
                        except sqlite3.IntegrityError:
                            pass
                        conn.close()
        except Exception as e:
            log.warning(f"[Scraper] Moneycontrol Earnings crash-protected: {e}. Falling back to empty set.")
            
        log.info(f"-> Logged {added} upcoming earnings from Moneycontrol.")
        return added

    def run_all(self):
        log.info("========== STARTING ULTIMATE SCRAPER (THREADPOOL) ==========")
        total_added = 0
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(self.scrape_rbi_rss),
                executor.submit(self.scrape_sebi_press_releases),
                executor.submit(self.scrape_yfinance_news),
                executor.submit(self.scrape_yfinance_actions),
                executor.submit(self.scrape_moneycontrol_earnings),
                executor.submit(self.scrape_et_markets_rss)
            ]
            
            for future in as_completed(futures):
                try:
                    result = future.result()
                    total_added += result
                except Exception as e:
                    log.error(f"Scraper task failed: {e}")
                    
        log.info(f"========== SCRAPE COMPLETE. Total New Items: {total_added} ==========")

if __name__ == "__main__":
    bot = UltimateScraper()
    bot.run_all()
