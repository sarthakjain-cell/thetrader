import sqlite3
import yfinance as yf
import pandas as pd
from abc import ABC, abstractmethod
from tenacity import retry, stop_after_attempt, wait_exponential
from logger import log

DB_PATH = "trading_system.db"

def save_bars_to_db(df):
    if df.empty: return
    try:
        conn = sqlite3.connect(DB_PATH, timeout=10)
        cursor = conn.cursor()
        
        # Drop rows with NaN values to prevent DB corruption
        df = df.dropna(subset=['Open', 'High', 'Low', 'Close', 'Volume'])
        if df.empty: return
        
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
            
    @retry(stop=stop_after_attempt(4), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _fetch_tv_data(self, symbol):
        from tvDatafeed import Interval
        tv_sym = symbol.replace('.NS', '')
        # Fetch ~100 bars to ensure we have the full current day
        return self.tv.get_hist(symbol=tv_sym, exchange='NSE', interval=Interval.in_5_minute, n_bars=100)

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=1, max=3))
    def _fetch_yf_data(self, symbol):
        df = yf.download(symbol, period="1d", interval="5m", progress=False)
        if df.empty:
            return None
            
        # Handle yfinance multi-index columns in recent versions
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(1)
            
        df.reset_index(inplace=True)
        # Rename just in case, though they are usually Title Case
        df.rename(columns={
            'Datetime': 'Datetime',
            'Open': 'Open',
            'High': 'High',
            'Low': 'Low',
            'Close': 'Close',
            'Volume': 'Volume'
        }, inplace=True)
        
        # Convert timezone
        if df['Datetime'].dt.tz is not None:
            df['Datetime'] = df['Datetime'].dt.tz_convert('Asia/Kolkata').dt.tz_localize(None)
            
        return df

    def get_today_data(self, symbols: list) -> dict:
        if not self.tv:
            log.error("TradingView not initialized.")
            return {}
            
        try:
            data_dict = {}
            today = pd.Timestamp.now('Asia/Kolkata').date()
            
            log.info(f"Downloading {len(symbols)} symbols from TradingView...")
            
            for sym in symbols:
                try:
                    # Fetch data with tenacious retries
                    df = None
                    try:
                        df = self._fetch_tv_data(sym)
                    except Exception as e:
                        log.warning(f"tvDatafeed failed for {sym}: {e}. Falling back to yfinance...")
                        df = self._fetch_yf_data(sym)
                    
                    if df is None or df.empty:
                        continue
                        
                    # If it came from TV, we need to process it
                    if df.index.name in ['datetime', 'Datetime', 'Date']:
                        df.reset_index(inplace=True)
                        
                    if 'datetime' in df.columns or df.columns.str.islower().any():
                        df.rename(columns={
                            'datetime': 'Datetime',
                            'open': 'Open',
                            'high': 'High',
                            'low': 'Low',
                            'close': 'Close',
                            'volume': 'Volume'
                        }, inplace=True)
                        
                        if df['Datetime'].dt.tz is None:
                            df['Datetime'] = df['Datetime'].dt.tz_localize('UTC').dt.tz_convert('Asia/Kolkata').dt.tz_localize(None)
                        else:
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

