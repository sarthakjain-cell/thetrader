import paramiko
import sqlite3
import pandas as pd
import os

IP = '206.189.129.232'
USER = 'root'
PASS = 'MyroomNo.is133g'

print("Connecting to Droplet to fetch database...")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    ssh.connect(IP, username=USER, password=PASS, timeout=10)
    sftp = ssh.open_sftp()
    remote_path = '/root/backend/trading_system.db'
    local_path = 'temp_trading_system.db'
    sftp.get(remote_path, local_path)
    sftp.close()
    ssh.close()
    
    print("Database downloaded. Analyzing PnL...")
    conn = sqlite3.connect(local_path)
    
    # Check paper_account equity
    acc = pd.read_sql("SELECT * FROM paper_account WHERE id=1", conn)
    if not acc.empty:
        equity = acc.iloc[0]['equity']
        print(f"Current Account Equity: Rs {equity:,.2f}")
    
    # Check paper_trades (closed trades)
    trades = pd.read_sql("SELECT * FROM paper_trades", conn)
    if not trades.empty:
        # Convert exit_time to datetime
        trades['exit_time'] = pd.to_datetime(trades['exit_time'])
        # Filter for today (2026-07-22 or latest date)
        latest_date = trades['exit_time'].dt.date.max()
        today_trades = trades[trades['exit_time'].dt.date == latest_date]
        
        total_pnl = today_trades['realized_pnl'].sum()
        wins = today_trades[today_trades['realized_pnl'] > 0]
        losses = today_trades[today_trades['realized_pnl'] <= 0]
        
        print(f"\n--- Trading Summary for {latest_date} ---")
        print(f"Total Trades: {len(today_trades)}")
        print(f"Winning Trades: {len(wins)}")
        print(f"Losing Trades: {len(losses)}")
        win_rate = (len(wins) / len(today_trades) * 100) if len(today_trades) > 0 else 0
        print(f"Win Rate: {win_rate:.1f}%")
        print(f"Net Realized PnL: Rs {total_pnl:,.2f}")
        
        print("\nTop Winners:")
        for _, row in wins.nlargest(5, 'realized_pnl').iterrows():
            print(f"  {row['symbol']} ({row.get('direction', 'LONG')}): +Rs {row['realized_pnl']:.2f}")
            
        print("\nTop Losers:")
        for _, row in losses.nsmallest(5, 'realized_pnl').iterrows():
            print(f"  {row['symbol']} ({row.get('direction', 'LONG')}): Rs {row['realized_pnl']:.2f}")
            
    else:
        print("No closed trades found.")
        
    # Check active positions
    pos = pd.read_sql("SELECT * FROM paper_positions", conn)
    if not pos.empty:
        print(f"\nCurrently holding {len(pos)} open positions.")
        for _, row in pos.iterrows():
            print(f"  {row['symbol']} ({row.get('direction', 'LONG')}) QTY: {row['qty']} @ {row['entry_price']}")
    else:
        print("\nNo open positions.")
        
    conn.close()
    if os.path.exists(local_path):
        os.remove(local_path)
        
except Exception as e:
    print(f"Error: {e}")
