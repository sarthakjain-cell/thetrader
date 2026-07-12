import sqlite3
import pandas as pd
import yfinance as yf
import os
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "trading_system.db")

def backfill_macro():
    print("Starting Macro Backfill (4 Years)...")
    tickers = {
        'vix': '^INDIAVIX',
        'crude': 'CL=F',
        'usd_inr': 'USDINR=X',
        'gspc': '^GSPC',
        'dji': '^DJI'
    }
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=4*365)
    
    master_df = pd.DataFrame()
    
    for name, sym in tickers.items():
        print(f"Fetching {sym}...")
        try:
            df = yf.Ticker(sym).history(start=start_date.strftime('%Y-%m-%d'), end=end_date.strftime('%Y-%m-%d'))
            if not df.empty:
                change_col = f"{name}_change"
                df[change_col] = df['Close'].pct_change() * 100.0
                
                df = df[[change_col]]
                df.index = df.index.tz_localize(None).normalize()
                
                if master_df.empty:
                    master_df = df
                else:
                    master_df = master_df.join(df, how='outer')
        except Exception as e:
            print(f"Error fetching {sym}: {e}")
            
    master_df = master_df.dropna(how='all')
    
    print(f"Backfill complete. Acquired {len(master_df)} rows. Inserting into DB...")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS global_macro_features (
            date TEXT PRIMARY KEY,
            vix_change REAL,
            crude_change REAL,
            usd_inr_change REAL,
            gspc_change REAL,
            dji_change REAL
        )
    ''')
    
    for idx, row in master_df.iterrows():
        date_str = idx.strftime('%Y-%m-%d')
        
        vix = row.get('vix_change')
        crude = row.get('crude_change')
        usd = row.get('usd_inr_change')
        gspc = row.get('gspc_change')
        dji = row.get('dji_change')
        
        def safe_float(val):
            return None if pd.isna(val) else float(val)
            
        cursor.execute('''
            INSERT OR REPLACE INTO global_macro_features 
            (date, vix_change, crude_change, usd_inr_change, gspc_change, dji_change)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            date_str,
            safe_float(vix),
            safe_float(crude),
            safe_float(usd),
            safe_float(gspc),
            safe_float(dji)
        ))
        
    conn.commit()
    conn.close()
    print("Database updated successfully.")

if __name__ == "__main__":
    backfill_macro()
