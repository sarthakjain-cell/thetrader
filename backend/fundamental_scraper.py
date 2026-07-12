import sqlite3
import pandas as pd
import yfinance as yf
from datetime import datetime
from zoneinfo import ZoneInfo
from logger import log
import os
import time
import random

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "trading_system.db")

NIFTY_SYMBOLS = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS",
    "KOTAKBANK.NS", "AXISBANK.NS", "SBIN.NS", "BAJFINANCE.NS", "ITC.NS",
    "LT.NS", "BHARTIARTL.NS", "HINDUNILVR.NS"
]

class FundamentalScraper:
    def __init__(self):
        self.init_db()

    def init_db(self):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS fundamental_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                symbol TEXT NOT NULL,
                pe_raw REAL,
                roe_raw REAL,
                de_raw REAL,
                rev_growth_raw REAL,
                op_margin_raw REAL,
                pe_pct REAL,
                roe_pct REAL,
                de_pct REAL,
                rev_growth_pct REAL,
                op_margin_pct REAL,
                fqs_score REAL,
                UNIQUE(date, symbol)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS fundamental_errors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                symbol TEXT NOT NULL,
                missing_fields TEXT NOT NULL
            )
        ''')
        conn.commit()
        conn.close()

    def run_fqs_generation(self):
        log.info("========== STARTING FUNDAMENTAL QUALITY SCORE GENERATION ==========")
        today_str = datetime.now(ZoneInfo('Asia/Kolkata')).strftime("%Y-%m-%d")
        
        raw_data = []
        
        for sym in NIFTY_SYMBOLS:
            log.info(f"[FQS] Fetching fundamental info for {sym}...")
            try:
                ticker = yf.Ticker(sym)
                info = ticker.info
                
                # Fetch raw metrics
                pe = info.get('trailingPE', None)
                roe = info.get('returnOnEquity', None)
                de = info.get('debtToEquity', None)
                rev_growth = info.get('revenueGrowth', None)
                op_margin = info.get('operatingMargins', None)
                
                missing_fields = []
                if pe is None: missing_fields.append("trailingPE")
                if roe is None: missing_fields.append("returnOnEquity")
                if de is None: missing_fields.append("debtToEquity")
                if rev_growth is None: missing_fields.append("revenueGrowth")
                if op_margin is None: missing_fields.append("operatingMargins")
                
                if missing_fields:
                    conn = sqlite3.connect(DB_PATH)
                    conn.cursor().execute("INSERT INTO fundamental_errors (date, symbol, missing_fields) VALUES (?, ?, ?)", 
                                          (today_str, sym, ",".join(missing_fields)))
                    conn.commit()
                    conn.close()
                    log.warning(f"[FQS] {sym} missing fields: {','.join(missing_fields)}")
                
                raw_data.append({
                    'symbol': sym,
                    'pe_raw': pe,
                    'roe_raw': roe,
                    'de_raw': de,
                    'rev_growth_raw': rev_growth,
                    'op_margin_raw': op_margin
                })
            except Exception as e:
                log.error(f"[FQS] Failed to fetch {sym}: {e}")
                
            time.sleep(random.uniform(1.0, 2.5))
            
        df = pd.DataFrame(raw_data)
        if df.empty:
            log.warning("No fundamental data fetched. Aborting FQS calculation.")
            return
            
        # Calculate percentiles using Pandas rank
        # rank(pct=True) assigns 0.0 to 1.0. We multiply by 100 for 0-100 score.
        
        # High is Good: ROE, Rev Growth, Op Margin
        df['roe_pct'] = df['roe_raw'].rank(pct=True, numeric_only=True) * 100
        df['rev_growth_pct'] = df['rev_growth_raw'].rank(pct=True, numeric_only=True) * 100
        df['op_margin_pct'] = df['op_margin_raw'].rank(pct=True, numeric_only=True) * 100
        
        # Low is Good: P/E, Debt/Equity. ascending=False means largest value gets rank 1% (lowest score), smallest gets 100%.
        df['pe_pct'] = df['pe_raw'].rank(pct=True, numeric_only=True, ascending=False) * 100
        df['de_pct'] = df['de_raw'].rank(pct=True, numeric_only=True, ascending=False) * 100
        
        # Fallback missing values to Neutral 50th Percentile
        pct_columns = ['roe_pct', 'rev_growth_pct', 'op_margin_pct', 'pe_pct', 'de_pct']
        for col in pct_columns:
            df[col] = df[col].fillna(50.0)
            
        # Weighted FQS Score
        # ROE (25%), D/E (20%), Rev Growth (20%), Op Margin (20%), P/E (15%)
        df['fqs_score'] = (
            df['roe_pct'] * 0.25 + 
            df['de_pct'] * 0.20 + 
            df['rev_growth_pct'] * 0.20 + 
            df['op_margin_pct'] * 0.20 + 
            df['pe_pct'] * 0.15
        )
        
        # Log to Database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        for idx, row in df.iterrows():
            try:
                cursor.execute('''
                    INSERT OR REPLACE INTO fundamental_data 
                    (date, symbol, pe_raw, roe_raw, de_raw, rev_growth_raw, op_margin_raw, 
                    pe_pct, roe_pct, de_pct, rev_growth_pct, op_margin_pct, fqs_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    today_str, row['symbol'],
                    row['pe_raw'] if pd.notnull(row['pe_raw']) else None,
                    row['roe_raw'] if pd.notnull(row['roe_raw']) else None,
                    row['de_raw'] if pd.notnull(row['de_raw']) else None,
                    row['rev_growth_raw'] if pd.notnull(row['rev_growth_raw']) else None,
                    row['op_margin_raw'] if pd.notnull(row['op_margin_raw']) else None,
                    row['pe_pct'], row['roe_pct'], row['de_pct'], row['rev_growth_pct'], row['op_margin_pct'],
                    row['fqs_score']
                ))
            except Exception as e:
                log.error(f"[FQS] Database insertion failed for {row['symbol']}: {e}")
                
        conn.commit()
        conn.close()
        
        log.info("========== FQS GENERATION COMPLETE ==========")
        # Print a quick summary leaderboard
        top_stocks = df.sort_values(by='fqs_score', ascending=False).head(3)
        log.info(f"Top 3 FQS Stocks Today: {', '.join(top_stocks['symbol'].tolist())}")


if __name__ == "__main__":
    scraper = FundamentalScraper()
    scraper.run_fqs_generation()
