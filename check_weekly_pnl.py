import sqlite3
import pandas as pd

local_path = 'temp_trading_system.db'

print("Analyzing PnL for the last 5 days...")
conn = sqlite3.connect(local_path)

trades = pd.read_sql("SELECT * FROM paper_trades", conn)
if not trades.empty:
    trades['exit_time'] = pd.to_datetime(trades['exit_time'])
    start_date = pd.to_datetime('2026-07-24').date()
    recent_trades = trades[trades['exit_time'].dt.date >= start_date]
    
    if recent_trades.empty:
        print("No trades taken in the last 5 days.")
    else:
        total_pnl = recent_trades['pnl'].sum()
        wins = recent_trades[recent_trades['pnl'] > 0]
        losses = recent_trades[recent_trades['pnl'] <= 0]
        
        print(f"\n--- Trading Summary (July 24 - Present) ---")
        print(f"Total Trades: {len(recent_trades)}")
        print(f"Winning Trades: {len(wins)}")
        print(f"Losing Trades: {len(losses)}")
        win_rate = (len(wins) / len(recent_trades) * 100) if len(recent_trades) > 0 else 0
        print(f"Win Rate: {win_rate:.1f}%")
        print(f"Net Realized PnL: Rs {total_pnl:,.2f}")
        
        print("\nDaily Breakdown:")
        daily_pnl = recent_trades.groupby(recent_trades['exit_time'].dt.date)['pnl'].sum()
        daily_count = recent_trades.groupby(recent_trades['exit_time'].dt.date).size()
        for date, pnl in daily_pnl.items():
            print(f"  {date}: Rs {pnl:,.2f} ({daily_count[date]} trades)")
        
        print("\nTop 5 Winners (Last 5 Days):")
        for _, row in wins.nlargest(5, 'pnl').iterrows():
            print(f"  {row['exit_time'].date()} | {row['symbol']}: +Rs {row['pnl']:.2f}")
            
        print("\nTop 5 Losers (Last 5 Days):")
        for _, row in losses.nsmallest(5, 'pnl').iterrows():
            print(f"  {row['exit_time'].date()} | {row['symbol']}: Rs {row['pnl']:.2f}")
else:
    print("No closed trades found.")
    
conn.close()
