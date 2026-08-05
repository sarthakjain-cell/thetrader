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
from datetime import datetime

conn = sqlite3.connect('/root/backend/trading_system.db')
print("--- ALL Open Positions ---")
df_open = pd.read_sql("SELECT * FROM paper_positions", conn)
print(df_open)

print("\\n--- ALL Closed Trades Today ---")
today = datetime.now().strftime('%Y-%m-%d')
try:
    df_closed = pd.read_sql(f"SELECT * FROM paper_trades WHERE date(exit_time) = '{today}'", conn)
    print(df_closed)
except Exception as e:
    print("Error reading paper_trades:", e)

conn.close()
"""
    sftp = ssh.open_sftp()
    with sftp.file('/root/check_db.py', 'w') as f:
        f.write(script)
    sftp.close()
    
    stdin, stdout, stderr = ssh.exec_command("/root/backend/venv/bin/python /root/check_db.py")
    print(stdout.read().decode())
    print(stderr.read().decode())
    
    ssh.close()
except Exception as e:
    print(f"Error: {e}")
