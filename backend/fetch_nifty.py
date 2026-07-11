import yfinance as yf
import pandas as pd
import sqlite3

ticker = "^NSEI"
df = yf.Ticker(ticker).history(period="5y", interval="1d")
df.reset_index(inplace=True)
if 'Date' in df.columns:
    df.rename(columns={'Date': 'Datetime'}, inplace=True)
df['Datetime'] = df['Datetime'].dt.strftime('%Y-%m-%d %H:%M:%S')
df['Symbol'] = ticker
df = df[['Datetime', 'Symbol', 'Open', 'High', 'Low', 'Close', 'Volume']]
df.ffill(inplace=True)
df.dropna(inplace=True)

conn = sqlite3.connect("trading_system.db")
df.to_sql("nifty_index", conn, if_exists="replace", index=False)
conn.close()
print("Nifty 50 Index saved to database.")
