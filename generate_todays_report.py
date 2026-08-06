import paramiko
from datetime import datetime
try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo

IP = "206.189.129.232"
USER = "root"
PASS = "MyroomNo.is133g"

def main():
    print(f"Connecting to {IP}...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(IP, username=USER, password=PASS, timeout=10)
    
    today = datetime.now(ZoneInfo('Asia/Kolkata')).strftime('%Y-%m-%d')
    print(f"\n=== REPORT FOR {today} ===")

    print("\n[1] PM2 STATUS")
    stdin, stdout, stderr = ssh.exec_command("pm2 status")
    print(stdout.read().decode('utf-8'))
    
    print(f"\n[2] TRADES AND PNL (DATE: {today})")
    query_closed = f"SELECT symbol, side, qty, entry_price, exit_price, pnl, strategy_id FROM paper_positions WHERE status='CLOSED' AND date(exit_time) = '{today}'"
    query_open = f"SELECT symbol, side, qty, entry_price, status, strategy_id FROM paper_positions WHERE status='OPEN'"
    
    python_cmd = f"""
import sqlite3
import pandas as pd

conn = sqlite3.connect('/root/backend/trading_system.db')
df_closed = pd.read_sql(\"{query_closed}\", conn)
df_open = pd.read_sql(\"{query_open}\", conn)

if df_closed.empty:
    print("No closed trades today.")
else:
    print("--- CLOSED TRADES ---")
    print(df_closed.to_string(index=False))
    print(f"\\nTOTAL REALIZED PNL TODAY: ₹{{df_closed['pnl'].sum():,.2f}}")
    wins = len(df_closed[df_closed['pnl'] > 0])
    losses = len(df_closed[df_closed['pnl'] <= 0])
    print(f"WIN RATE: {{(wins/len(df_closed))*100:.1f}}% ({{wins}} W / {{losses}} L)")

if df_open.empty:
    print("\\nNo open trades right now.")
else:
    print("\\n--- OPEN POSITIONS ---")
    print(df_open.to_string(index=False))

conn.close()
"""
    stdin, stdout, stderr = ssh.exec_command(f"python3 -c \"{python_cmd}\"")
    print(stdout.read().decode('utf-8'))
    err = stderr.read().decode('utf-8')
    if err:
        print("ERRORS:")
        print(err)

    print("\n[3] ENGINE ERRORS (IF ANY)")
    stdin, stdout, stderr = ssh.exec_command("tail -n 10 /root/.pm2/logs/engine-a-technical-error.log /root/.pm2/logs/engine-b-sentiment-error.log /root/.pm2/logs/ai-brain-daemon-error.log")
    print(stdout.read().decode('utf-8'))

    ssh.close()

if __name__ == "__main__":
    main()
