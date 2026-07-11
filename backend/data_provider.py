import sqlite3
import yfinance as yf
import pandas as pd
from abc import ABC, abstractmethod
from logger import log

DB_PATH = "trading_system.db"

def save_bars_to_db(df):
    if df.empty: return
    try:
        conn = sqlite3.connect(DB_PATH, timeout=10)
        cursor = conn.cursor()
        for _, row in df.iterrows():
            cursor.execute('''
                INSERT OR REPLACE INTO intraday_5m 
                (symbol, datetime, open, high, low, close, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (row['Symbol'], str(row['Datetime']), row['Open'], row['High'], row['Low'], row['Close'], row['Volume']))
        conn.commit()
        conn.close()
    except Exception as e:
        log.error(f"Error saving bars to db: {e}")

class DataProvider(ABC):
    @abstractmethod
    def get_today_data(self, symbol):
        """Returns 5m candles for the current trading day up to the latest completed bar."""
        pass

class YFinanceProvider(DataProvider):
    def get_today_data(self, symbol):
        try:
            stock = yf.Ticker(symbol)
            # Fetch last 2 days just to be safe with timezone boundaries, then filter today
            df = stock.history(period="2d", interval="5m")
            if df.empty:
                return pd.DataFrame()
                
            df.reset_index(inplace=True)
            if 'Datetime' not in df.columns and 'Date' in df.columns:
                df.rename(columns={'Date': 'Datetime'}, inplace=True)
                
            # Convert to naive datetime for consistency if it's tz-aware
            if df['Datetime'].dt.tz is not None:
                df['Datetime'] = df['Datetime'].dt.tz_convert('Asia/Kolkata').dt.tz_localize(None)
                
            # Filter for today only
            today = pd.Timestamp.now('Asia/Kolkata').date()
            df = df[df['Datetime'].dt.date == today].copy()
            
            if df.empty:
                return pd.DataFrame()
                
            df['Symbol'] = symbol
            df = df[['Datetime', 'Symbol', 'Open', 'High', 'Low', 'Close', 'Volume']]
            
            # Save fetched bars to DB for frontend charting
            save_bars_to_db(df)
            
            return df
        except Exception as e:
            log.error(f"Error fetching YFinance data for {symbol}: {e}")
            return pd.DataFrame()
