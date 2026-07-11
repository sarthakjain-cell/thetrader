import os
import requests
import pandas as pd
from datetime import datetime, timedelta
import sqlite3
import time
from logger import log

DB_PATH = "trading_system.db"

def get_token():
    try:
        with open("upstox_token.txt", "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        log.error("Token not found. Please run auth.py first to authenticate.")
        exit(1)

def fetch_upstox_data(instrument_key, from_date, to_date, interval="1minute"):
    token = get_token()
    url = f"https://api.upstox.com/v2/historical-candle/{instrument_key}/{interval}/{to_date}/{from_date}"
    
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    
    log.info(f"Fetching {interval} data for {instrument_key} from {from_date} to {to_date}")
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        if 'data' in data and data['data'] and 'candles' in data['data']:
            candles = data['data']['candles']
            # Upstox format: [timestamp, open, high, low, close, volume, open_interest]
            df = pd.DataFrame(candles, columns=['Datetime', 'Open', 'High', 'Low', 'Close', 'Volume', 'OI'])
            df['Datetime'] = pd.to_datetime(df['Datetime'])
            
            # Upstox returns newest first, so we reverse it to chronological order
            df = df.iloc[::-1].reset_index(drop=True)
            return df
        else:
            log.warning(f"No data returned for period: {from_date} to {to_date}")
            return pd.DataFrame()
    elif response.status_code == 401:
        log.error("Unauthorized. Your Upstox token has expired or is invalid. Re-run auth.py.")
        exit(1)
    else:
        log.error(f"Error fetching data: {response.text}")
        return pd.DataFrame()

def save_to_db(df, table_name="historical_data"):
    if df.empty:
        return
        
    conn = sqlite3.connect(DB_PATH)
    # Save raw dataframe to sqlite
    df.to_sql(table_name, conn, if_exists="replace", index=False)
    conn.close()
    log.info(f"Saved {len(df)} rows to database table '{table_name}'.")

def fetch_multi_year_data(instrument_key="NSE_EQ|INE002A01018", years=5, interval="5minute"):
    # Default: INE002A01018 is Reliance Industries EQ
    end_date = datetime.now()
    start_date = end_date - timedelta(days=years*365)
    
    # Upstox historical API requires chunking (e.g., max 6 months or 1 year per call)
    # We paginate backwards in 100-day chunks to be perfectly safe against API row limits
    
    current_end = end_date
    all_data = []
    
    log.info(f"Starting {years}-year continuous data fetch for {instrument_key}...")
    
    while current_end > start_date:
        current_start = current_end - timedelta(days=100)
        if current_start < start_date:
            current_start = start_date
            
        str_to_date = current_end.strftime("%Y-%m-%d")
        str_from_date = current_start.strftime("%Y-%m-%d")
        
        df_chunk = fetch_upstox_data(instrument_key, str_from_date, str_to_date, interval)
        if not df_chunk.empty:
            all_data.append(df_chunk)
            
        # Move the window back
        current_end = current_start - timedelta(days=1)
        
        # Respect API rate limits (Wait 1 second between requests)
        time.sleep(1)
        
    if all_data:
        # Concat all chunks (which are ordered newest to oldest in chunks, but internal rows are oldest to newest)
        # So we concat, then sort by Datetime globally.
        final_df = pd.concat(all_data, ignore_index=True)
        final_df.sort_values(by='Datetime', inplace=True)
        final_df.drop_duplicates(subset=['Datetime'], inplace=True)
        
        log.info(f"Success! Fetched a total of {len(final_df)} continuous {interval} candles.")
        save_to_db(final_df, table_name="reliance_5m_historical")
        return final_df
    else:
        log.error("Failed to fetch any data.")
        return pd.DataFrame()

if __name__ == "__main__":
    fetch_multi_year_data()
