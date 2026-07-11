import yfinance as yf
import pandas as pd
import sqlite3
import time
from logger import log

DB_PATH = "trading_system.db"
TABLE_NAME = "market_data_5m"

NIFTY_SYMBOLS = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS",
    "KOTAKBANK.NS", "AXISBANK.NS", "SBIN.NS", "BAJFINANCE.NS", "ITC.NS",
    "LT.NS", "BHARTIARTL.NS", "HINDUNILVR.NS", "^NSEI"
]

def initialize_database():
    """Drops the existing multi-asset table to start fresh."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(f"DROP TABLE IF EXISTS {TABLE_NAME}")
    conn.commit()
    conn.close()
    log.info(f"Database initialized. Cleared old table: {TABLE_NAME}")

def fetch_and_store_multi_asset(symbols, period="5y", interval="1d"):
    log.info(f"Initiating Multi-Asset Data Fetch: {len(symbols)} symbols over {period} ({interval} candles).")
    
    initialize_database()
    conn = sqlite3.connect(DB_PATH)
    
    total_rows = 0
    failed_symbols = []

    for symbol in symbols:
        log.info(f"Fetching data for {symbol}...")
        try:
            stock = yf.Ticker(symbol)
            df = stock.history(period=period, interval=interval)
            
            if df.empty:
                log.warning(f"No data returned for {symbol}. Skipping.")
                failed_symbols.append(symbol)
                continue
                
            df.reset_index(inplace=True)
            
            # Standardize Datetime column
            if 'Date' in df.columns:
                df.rename(columns={'Date': 'Datetime'}, inplace=True)
            df['Datetime'] = df['Datetime'].dt.strftime('%Y-%m-%d %H:%M:%S')
            
            # Add Symbol column for multi-asset identification
            df['Symbol'] = symbol
            
            # Clean up and keep necessary columns
            df = df[['Datetime', 'Symbol', 'Open', 'High', 'Low', 'Close', 'Volume']]
            
            # Handle missing data (forward fill, then drop)
            df.ffill(inplace=True)
            df.dropna(inplace=True)
            
            # Append to SQLite table
            df.to_sql(TABLE_NAME, conn, if_exists="append", index=False)
            
            total_rows += len(df)
            log.info(f"✓ Saved {len(df)} rows for {symbol}.")
            
            # Polite delay to respect Yahoo Finance API rate limits
            time.sleep(1)
            
        except Exception as e:
            log.error(f"Error fetching {symbol}: {e}")
            failed_symbols.append(symbol)
            
    conn.close()
    
    log.info(f"--- FETCH COMPLETE ---")
    log.info(f"Total Rows Saved: {total_rows} across {len(symbols) - len(failed_symbols)} assets.")
    if failed_symbols:
        log.warning(f"Failed Symbols: {failed_symbols}")

if __name__ == "__main__":
    fetch_and_store_multi_asset(NIFTY_SYMBOLS, period="60d", interval="5m")
