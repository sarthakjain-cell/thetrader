import sys
sys.path.append('/root/backend')
from data_provider import TradingViewProvider

p = TradingViewProvider()
# Force yfinance by setting tv to None
p.tv = None

try:
    df = p._fetch_yf_data("JSWSTEEL.NS")
    print(df.columns.tolist())
    print("SUCCESS")
except Exception as e:
    import traceback
    traceback.print_exc()
