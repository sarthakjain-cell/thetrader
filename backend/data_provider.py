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
        
        # Optimize memory and CPU using bulk transaction
        records = [
            (row['Symbol'], str(row['Datetime']), row['Open'], row['High'], row['Low'], row['Close'], row['Volume'])
            for _, row in df.iterrows()
        ]
        
        cursor.executemany('''
            INSERT OR REPLACE INTO intraday_5m 
            (symbol, datetime, open, high, low, close, volume)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', records)
        
        conn.commit()
        conn.close()
    except Exception as e:
        log.error(f"Error saving bars to db: {e}")

class DataProvider(ABC):
    @abstractmethod
    def get_today_data(self, symbols: list) -> dict:
        """Returns a dict of symbol -> 5m candles DataFrame for the current trading day."""
        pass

class TradingViewProvider(DataProvider):
    def __init__(self):
        try:
            from tvDatafeed import TvDatafeed
            # Initialize without login for free public data
            self.tv = TvDatafeed()
        except Exception as e:
            log.error(f"Failed to initialize TradingView: {e}")
            self.tv = None
            
    def get_today_data(self, symbols: list) -> dict:
        if not self.tv:
            log.error("TradingView not initialized.")
            return {}
            
        try:
            from tvDatafeed import Interval
            data_dict = {}
            today = pd.Timestamp.now('Asia/Kolkata').date()
            
            log.info(f"Downloading {len(symbols)} symbols from TradingView...")
            
            for sym in symbols:
                try:
                    # Remove .NS for TradingView symbol, and specify NSE exchange
                    tv_sym = sym.replace('.NS', '')
                    # Fetch ~100 bars to ensure we have the full current day
                    df = self.tv.get_hist(symbol=tv_sym, exchange='NSE', interval=Interval.in_5_minute, n_bars=100)
                    
                    if df is None or df.empty:
                        continue
                        
                    # tvDatafeed returns index as datetime, columns: symbol, open, high, low, close, volume
                    df.reset_index(inplace=True)
                    df.rename(columns={
                        'datetime': 'Datetime',
                        'open': 'Open',
                        'high': 'High',
                        'low': 'Low',
                        'close': 'Close',
                        'volume': 'Volume'
                    }, inplace=True)
                    
                    # Convert timezone to naive
                    if df['Datetime'].dt.tz is not None:
                        df['Datetime'] = df['Datetime'].dt.tz_convert('Asia/Kolkata').dt.tz_localize(None)
                        
                    # Filter for today only
                    df = df[df['Datetime'].dt.date == today].copy()
                    
                    if df.empty:
                        continue
                        
                    df['Symbol'] = sym # Restore original .NS symbol for the rest of our engine
                    df = df[['Datetime', 'Symbol', 'Open', 'High', 'Low', 'Close', 'Volume']]
                    
                    # Save to DB for charting
                    save_bars_to_db(df)
                    
                    data_dict[sym] = df
                except Exception as e:
                    log.error(f"Failed to fetch {sym} from TV: {e}")
                    
            return data_dict
        except Exception as e:
            log.error(f"Fatal error in TradingViewProvider: {e}")
            return {}

