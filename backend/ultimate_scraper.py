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

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "trading_system.db")

NIFTY_SYMBOLS = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS",
    "KOTAKBANK.NS", "AXISBANK.NS", "SBIN.NS", "BAJFINANCE.NS", "ITC.NS",
    "LT.NS", "BHARTIARTL.NS", "HINDUNILVR.NS"
]

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

    def init_db(self):
        conn = sqlite3.connect(DB_PATH)
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
        
        conn = sqlite3.connect(DB_PATH)
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
                
            # Be polite to Yahoo Finance APIs
            time.sleep(random.uniform(0.5, 1.5))
            
        return added

    def run_all(self):
        log.info("========== STARTING ULTIMATE SCRAPER ==========")
        total_added = 0
        
        # 1. Macro Policy
        rbi_added = self.scrape_rbi_rss()
        log.info(f"-> Acquired {rbi_added} new RBI macro updates.")
        total_added += rbi_added
        
        # 2. Regulatory Limits
        sebi_added = self.scrape_sebi_press_releases()
        log.info(f"-> Acquired {sebi_added} new SEBI regulations.")
        total_added += sebi_added
        
        # 3. Market Sentiment
        yf_added = self.scrape_yfinance_news()
        log.info(f"-> Acquired {yf_added} new Financial News headlines.")
        total_added += yf_added
        
        log.info(f"========== SCRAPE COMPLETE. Total New Items: {total_added} ==========")

if __name__ == "__main__":
    bot = UltimateScraper()
    bot.run_all()
