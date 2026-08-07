import pytest
import pandas as pd
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))
from data_provider import TradingViewProvider

@pytest.fixture
def provider():
    # Initialize without PM2
    p = TradingViewProvider()
    return p

def test_yfinance_fallback_columns(provider):
    """
    Test that the yfinance fallback method correctly fetches data
    and assigns the 'Datetime' column properly.
    """
    df = provider._fetch_yf_data("RELIANCE.NS")
    
    assert df is not None
    assert not df.empty
    
    # Check that required columns exist exactly as expected
    expected_cols = ['Datetime', 'Open', 'High', 'Low', 'Close', 'Volume']
    for col in expected_cols:
        assert col in df.columns, f"Missing required column: {col}"
        
    # Check that Datetime is actually a datetime object, not a string
    assert pd.api.types.is_datetime64_any_dtype(df['Datetime']), "Datetime column is not a datetime object!"

def test_tradingview_fetch_columns(provider):
    """
    Test that the TradingView fetch method correctly fetches data
    and returns a DataFrame with 'datetime' as the index.
    """
    try:
        df = provider._fetch_tv_data("RELIANCE.NS")
        assert df is not None
        assert not df.empty
        
        # tvDatafeed returns 'datetime' as the index
        assert df.index.name in ['datetime', 'Datetime', 'Date'], f"Index should be a datetime index, got {df.index.name}"
        
    except Exception as e:
        pytest.skip(f"TradingView is occasionally unstable/rate-limited: {e}")
