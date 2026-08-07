import pandas as pd
import yfinance as yf
from abc import ABC
from data_provider import DataProvider
from logger import log
import os

class MockDataProvider(DataProvider):
    """
    A data provider for offline simulation / mock training.
    It downloads data for a specific historical date (default: today) and caches it.
    When get_today_data() is called, it returns the data sliced up to self.current_time.
    """
    def __init__(self, simulation_date: str):
        """
        simulation_date: 'YYYY-MM-DD'
        """
        self.simulation_date = pd.to_datetime(simulation_date).date()
        self.current_time = None
        self.cached_data = {}
        self.cache_dir = "mock_cache"
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
            
    def preload_data(self, symbols: list):
        log.info(f"MockDataProvider: Preloading data for {len(symbols)} symbols on {self.simulation_date}...")
        for sym in symbols:
            cache_file = os.path.join(self.cache_dir, f"{sym}_{self.simulation_date}.csv")
            if os.path.exists(cache_file):
                df = pd.read_csv(cache_file, parse_dates=['Datetime'])
                self.cached_data[sym] = df
            else:
                try:
                    df = yf.download(sym, period="5d", interval="5m", progress=False)
                    if df.empty:
                        continue
                    if isinstance(df.columns, pd.MultiIndex):
                        df.columns = df.columns.droplevel(1)
                    df.reset_index(inplace=True)
                    df.rename(columns={
                        'Datetime': 'Datetime', 'Open': 'Open', 'High': 'High',
                        'Low': 'Low', 'Close': 'Close', 'Volume': 'Volume'
                    }, inplace=True)
                    if df['Datetime'].dt.tz is not None:
                        df['Datetime'] = df['Datetime'].dt.tz_convert('Asia/Kolkata').dt.tz_localize(None)
                    
                    # Filter for simulation date
                    df = df[df['Datetime'].dt.date == self.simulation_date].copy()
                    
                    if not df.empty:
                        df['Symbol'] = sym
                        df = df[['Datetime', 'Symbol', 'Open', 'High', 'Low', 'Close', 'Volume']]
                        df.to_csv(cache_file, index=False)
                        self.cached_data[sym] = df
                except Exception as e:
                    log.error(f"Failed to preload {sym}: {e}")

    def get_today_data(self, symbols: list) -> dict:
        if not self.current_time:
            log.error("MockDataProvider: current_time is not set!")
            return {}
            
        sliced_data = {}
        for sym in symbols:
            df = self.cached_data.get(sym)
            if df is not None and not df.empty:
                # Slice data up to the simulated current time
                mask = df['Datetime'] <= self.current_time
                df_sliced = df[mask].copy()
                if not df_sliced.empty:
                    sliced_data[sym] = df_sliced
        return sliced_data
