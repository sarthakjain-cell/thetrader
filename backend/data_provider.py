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
    def get_today_data(self, symbols: list) -> dict:
        """Returns a dict of symbol -> 5m candles DataFrame for the current trading day."""
        pass

class YFinanceProvider(DataProvider):
    def get_today_data(self, symbols: list) -> dict:
        try:
            tickers_str = " ".join(symbols)
            log.info(f"Batch downloading {len(symbols)} symbols...")
            
            # Fetch last 2 days just to be safe with timezone boundaries
            df_raw = yf.download(tickers=tickers_str, period="2d", interval="5m", group_by="ticker", progress=False)
            
            if df_raw.empty:
                return {}
                
            data_dict = {}
            today = pd.Timestamp.now('Asia/Kolkata').date()
            
            for sym in symbols:
                if len(symbols) == 1:
                    df = df_raw.copy()
                else:
                    try:
                        df = df_raw[sym].copy()
                    except KeyError:
                        continue
                        
                df = df.dropna(how='all')
                if df.empty:
                    continue
                    
                df.reset_index(inplace=True)
                if 'Datetime' not in df.columns and 'Date' in df.columns:
                    df.rename(columns={'Date': 'Datetime'}, inplace=True)
                    
                # Convert to naive datetime for consistency if it's tz-aware
                if df['Datetime'].dt.tz is not None:
                    df['Datetime'] = df['Datetime'].dt.tz_convert('Asia/Kolkata').dt.tz_localize(None)
                    
                # Filter for today only
                df = df[df['Datetime'].dt.date == today].copy()
                
                if df.empty:
                    continue
                    
                df['Symbol'] = sym
                df = df[['Datetime', 'Symbol', 'Open', 'High', 'Low', 'Close', 'Volume']]
                
                # Save fetched bars to DB for frontend charting
                save_bars_to_db(df)
                
                data_dict[sym] = df
                
            return data_dict
        except Exception as e:
            log.error(f"Error fetching YFinance batched data: {e}")
            return {}

