import paramiko

IP = '206.189.129.232'
USER = 'root'
PASS = 'MyroomNo.is133g'

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(IP, username=USER, password=PASS, timeout=10)
    
    script = """
import sqlite3
import pandas as pd

conn = sqlite3.connect('/root/backend/trading_system.db')
print("Total open pos:", pd.read_sql("SELECT COUNT(*) FROM paper_positions", conn).iloc[0,0])
print("Today's open pos:", pd.read_sql("SELECT COUNT(*) FROM paper_positions WHERE date(entry_time) = '2026-08-05'", conn).iloc[0,0])
print("Total closed trades:", pd.read_sql("SELECT COUNT(*) FROM paper_trades", conn).iloc[0,0])
print("--- Today's Closed Trades ---")
print(pd.read_sql("SELECT symbol, strategy_id, entry_time, exit_time, entry_price, exit_price, pnl FROM paper_trades WHERE date(exit_time) = '2026-08-05'", conn).to_string(index=False))

"""
    sftp = ssh.open_sftp()
    with sftp.file('/root/check_counts.py', 'w') as f:
        f.write(script)
    sftp.close()
    
    stdin, stdout, stderr = ssh.exec_command("/root/backend/venv/bin/python /root/check_counts.py")
    print(stdout.read().decode())
    ssh.close()
except Exception as e:
    print(f"Error: {e}")
