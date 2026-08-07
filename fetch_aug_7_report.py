import paramiko
import pandas as pd
import io

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('206.189.129.232', username='root', password='MyroomNo.is133g')

# Query for today's date (Aug 7)
date_str = '2026-08-07'

query_closed = f"SELECT symbol, entry_time, exit_time, entry_price, exit_price, qty, pnl, status, strategy_id FROM paper_trades WHERE date(entry_time) = '{date_str}';"
stdin, stdout, stderr = ssh.exec_command(f'sqlite3 /root/backend/trading_system.db -header -csv "{query_closed}"')
out_closed = stdout.read().decode().strip()

query_open = f"SELECT symbol, entry_time, entry_price, qty, strategy_id FROM paper_positions WHERE date(entry_time) = '{date_str}';"
stdin, stdout, stderr = ssh.exec_command(f'sqlite3 /root/backend/trading_system.db -header -csv "{query_open}"')
out_open = stdout.read().decode().strip()

print("=== OPEN POSITIONS ===")
if out_open and len(out_open.split('\\n')) > 1:
    df_open = pd.read_csv(io.StringIO(out_open))
    print(df_open.to_markdown(index=False))
else:
    print("No open positions today.")

print("\\n=== CLOSED TRADES ===")
if out_closed and len(out_closed.split('\\n')) > 1:
    df_closed = pd.read_csv(io.StringIO(out_closed))
    print(df_closed.to_markdown(index=False))
    
    total_pnl = df_closed['pnl'].sum()
    print(f"\\nTotal Realized PnL: INR {total_pnl:.2f}")
    
    wins = len(df_closed[df_closed['pnl'] > 0])
    losses = len(df_closed[df_closed['pnl'] <= 0])
    print(f"Wins: {wins}, Losses: {losses}")
else:
    print("No closed trades today.")
    print("\\nTotal Realized PnL: INR 0.00")

ssh.close()
