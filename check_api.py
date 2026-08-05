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
import json

conn = sqlite3.connect('/root/backend/trading_system.db')
today = pd.Timestamp.now('Asia/Kolkata').strftime('%Y-%m-%d')
trades_df = pd.read_sql(f"SELECT * FROM paper_trades WHERE exit_time LIKE '{today}%'", conn)

print("Number of trades fetched by API:", len(trades_df))
if not trades_df.empty:
    print(trades_df.head(2))
    
conn.close()
"""
    sftp = ssh.open_sftp()
    with sftp.file('/root/test_api_logic.py', 'w') as f:
        f.write(script)
    sftp.close()
    
    stdin, stdout, stderr = ssh.exec_command("/root/backend/venv/bin/python /root/test_api_logic.py")
    print(stdout.read().decode('utf-8'))
    
    ssh.close()
except Exception as e:
    print(f"Error: {e}")
