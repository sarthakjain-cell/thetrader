import yfinance as yf
import pandas as pd
import os

def fetch_historical_data(ticker_symbol, period="5d", interval="5m"):
    print(f"Fetching {period} of {interval} data for {ticker_symbol}...")
    ticker = yf.Ticker(ticker_symbol)
    
    # Download historical data
    df = ticker.history(period=period, interval=interval)
    
    if df.empty:
        print("No data found. Check the ticker symbol.")
        return
        
    # Clean up the dataframe
    df.reset_index(inplace=True)
    
    # Save to CSV in a data folder
    os.makedirs("data", exist_ok=True)
    file_path = f"data/{ticker_symbol}_{period}_{interval}.csv"
    df.to_csv(file_path, index=False)
    
    print(f"Successfully downloaded {len(df)} rows of data!")
    print(f"Saved to: {file_path}")
    
    # Print the first few rows to verify
    print("\nSample Data:")
    print(df[['Datetime', 'Open', 'High', 'Low', 'Close', 'Volume']].head())

if __name__ == "__main__":
    # RELIANCE.NS is Reliance Industries on the National Stock Exchange of India
    fetch_historical_data("RELIANCE.NS", period="5d", interval="5m")
