import yfinance as yf
import pandas as pd
import sqlite3

DB_PATH = "trading_system.db"

def fetch_60d_data():
    conn = sqlite3.connect(DB_PATH)
    
    # We will fetch RELIANCE.NS as the backtest instrument
    symbol = "RELIANCE.NS"
    print(f"Fetching 60 days of 5m data for {symbol}...")
    
    ticker = yf.Ticker(symbol)
    df = ticker.history(period="60d", interval="5m")
    
    if df.empty:
        print("Failed to fetch data.")
        return
        
    df.reset_index(inplace=True)
    if 'Datetime' not in df.columns and 'Date' in df.columns:
        df.rename(columns={'Date': 'Datetime'}, inplace=True)
        
    if df['Datetime'].dt.tz is not None:
        df['Datetime'] = df['Datetime'].dt.tz_convert('Asia/Kolkata').dt.tz_localize(None)
        
    df['Datetime'] = df['Datetime'].astype(str)
    
    # Save to the table `historical_data_5y` (which is what walk_forward uses)
    df.to_sql("historical_data_5y", conn, if_exists="replace", index=False)
    
    print(f"Successfully saved {len(df)} rows to local DB.")
    conn.close()

if __name__ == "__main__":
    fetch_60d_data()
