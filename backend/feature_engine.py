import pandas as pd
import numpy as np
import ta

def compute_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes technical indicators and features for the given OHLCV DataFrame.
    Expects columns: Open, High, Low, Close, Volume.
    The data should be in chronological order.
    Returns a copy of the dataframe with new feature columns.
    """
    df = df.copy()
    
    # 1. EMAs
    df['EMA_9'] = ta.trend.ema_indicator(df['Close'], window=9)
    df['EMA_21'] = ta.trend.ema_indicator(df['Close'], window=21)
    
    # 2. RSI
    df['RSI_14'] = ta.momentum.rsi(df['Close'], window=14)
    
    # 3. ATR
    atr_ind = ta.volatility.AverageTrueRange(df['High'], df['Low'], df['Close'], window=14)
    df['ATR_14'] = atr_ind.average_true_range()
    
    # Fallback for ATR if calculated as 0
    df['ATR_14'] = np.where(df['ATR_14'] == 0, df['Close'] * 0.005, df['ATR_14'])
    
    # 4. ADX
    adx_ind = ta.trend.ADXIndicator(df['High'], df['Low'], df['Close'], window=14)
    df['ADX_14'] = adx_ind.adx()
    
    # 5. VWAP (Intraday)
    # Assumes df index is Datetime or there's a 'Datetime' column to group by day
    # For now, if we pass daily chunks to feature_engine, we just do a rolling cumulative sum
    typical_price = (df['High'] + df['Low'] + df['Close']) / 3
    df['VWAP'] = (typical_price * df['Volume']).cumsum() / df['Volume'].cumsum()
    
    # 6. ORB High/Low (30 mins = first 6 bars if 5-min timeframe)
    # Since we evaluate row-by-row, we need a column that holds the ORB High/Low for the day
    if len(df) >= 6:
        orb_high = df['High'].iloc[:6].max()
        orb_low = df['Low'].iloc[:6].min()
    else:
        # If less than 6 bars, ORB isn't fully formed
        orb_high = df['High'].max()
        orb_low = df['Low'].min()
        
    df['ORB_High'] = orb_high
    df['ORB_Low'] = orb_low
    
    # 7. Volume SMA
    df['Volume_SMA_20'] = df['Volume'].rolling(window=20).mean()
    
    # 8. Previous Close (Simulated for gap down)
    df['Prev_Close'] = df['Close'].shift(1)
    
    # 9. --- CANDLESTICK PATTERN RECOGNITION (Vectorized) ---
    body = (df['Open'] - df['Close']).abs()
    high_low = df['High'] - df['Low']
    
    # Doji: Body is less than 10% of the entire candle range
    df['CDL_Doji'] = (body <= (high_low * 0.1)).astype(int)
    
    # Bullish Hammer / Pin Bar
    lower_wick = df[['Open', 'Close']].min(axis=1) - df['Low']
    upper_wick = df['High'] - df[['Open', 'Close']].max(axis=1)
    df['CDL_Hammer'] = (
        (lower_wick > 2 * body) & 
        (upper_wick < body) & 
        (high_low > df['ATR_14'] * 0.5)
    ).astype(int)
    
    # Bearish Shooting Star
    df['CDL_Shooting_Star'] = (
        (upper_wick > 2 * body) &
        (lower_wick < body) &
        (high_low > df['ATR_14'] * 0.5)
    ).astype(int)
    
    # Marubozu (Solid Body, negligible wicks)
    df['CDL_Marubozu'] = (
        (upper_wick <= (high_low * 0.05)) & 
        (lower_wick <= (high_low * 0.05)) &
        (body > df['ATR_14'] * 0.5)
    ).astype(int)
    
    # Bullish Engulfing
    prev_open = df['Open'].shift(1)
    prev_close = df['Close'].shift(1)
    df['CDL_Engulfing_Bull'] = (
        (prev_open > prev_close) &          # Prev is Red
        (df['Close'] > df['Open']) &        # Curr is Green
        (df['Close'] > prev_open) &         # Curr closes above prev open
        (df['Open'] < prev_close)           # Curr opens below prev close
    ).astype(int)
    
    # Inside Bar
    prev_high = df['High'].shift(1)
    prev_low = df['Low'].shift(1)
    df['CDL_Inside_Bar'] = (
        (df['High'] < prev_high) & 
        (df['Low'] > prev_low)
    ).astype(int)
    
    return df
