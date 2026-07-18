from data_provider import YFinanceProvider
from live_trader import SYMBOLS

provider = YFinanceProvider()
print(f"Fetching {len(SYMBOLS)} symbols in batch mode...")
data = provider.get_today_data(SYMBOLS)

if data:
    print(f"Successfully fetched data for {len(data)} symbols.")
    for sym, df in list(data.items())[:3]:
        print(f"\n{sym} Data Shape: {df.shape}")
        print(df.tail(1))
else:
    print("Failed to fetch data or no data available today.")
