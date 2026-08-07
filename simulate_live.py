import sys
import os
import shutil
import pandas as pd
from datetime import datetime, timedelta

sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
import live_trader
from mock_data_provider import MockDataProvider
from live_trader import SYMBOLS

# 1. Setup Mock DB to avoid polluting real trades
MOCK_DB = os.path.join(os.path.dirname(__file__), 'backend', 'mock_trading.db')
REAL_DB = os.path.join(os.path.dirname(__file__), 'backend', 'trading_system.db')

if os.path.exists(REAL_DB):
    shutil.copy2(REAL_DB, MOCK_DB)
else:
    print(f"Real DB not found at {REAL_DB}")
    sys.exit(1)

# Override the DB path inside live_trader
live_trader.DB_PATH = MOCK_DB

# 2. Setup Mock Data Provider
# Let's simulate today (Aug 7)
SIM_DATE_STR = '2026-08-07'
print(f"=== Starting Mock Train for {SIM_DATE_STR} ===")
mock_provider = MockDataProvider(SIM_DATE_STR)
mock_provider.preload_data(SYMBOLS)

# 3. Initialize Engine
engine = live_trader.MultiStrategyEngine()
engine.provider = mock_provider

# 4. Run Simulation Loop
# Market hours: 09:15 to 15:30 IST
sim_date = pd.to_datetime(SIM_DATE_STR).date()
start_time = datetime.combine(sim_date, datetime.strptime("09:15", "%H:%M").time())
end_time = datetime.combine(sim_date, datetime.strptime("15:30", "%H:%M").time())

current_time = start_time
print("Running simulation loop...")

while current_time <= end_time:
    # Tell the mock provider what time it currently is
    mock_provider.current_time = current_time
    
    # Process tick
    engine.process_tick(now=current_time)
    
    # Advance time by 5 minutes
    current_time += timedelta(minutes=5)

# 5. Report Results
print("=== Mock Train Complete ===")
import sqlite3
conn = sqlite3.connect(MOCK_DB)
df = pd.read_sql(f"SELECT symbol, entry_time, exit_time, pnl, strategy_id FROM paper_trades WHERE date(entry_time) = '{SIM_DATE_STR}'", conn)
if not df.empty:
    print(df.to_markdown(index=False))
    print(f"\\nTotal Simulated PnL: INR {df['pnl'].sum():.2f}")
else:
    print("No trades were taken during the simulation.")
conn.close()

# Cleanup
if os.path.exists(MOCK_DB):
    os.remove(MOCK_DB)
