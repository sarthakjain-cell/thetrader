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
conn = sqlite3.connect('/root/trading_system.db')
df = pd.read_sql("SELECT strategy_id, config_json, is_active FROM generated_strategies LIMIT 5", conn)
print(df.to_string())
"""
    sftp = ssh.open_sftp()
    with sftp.file('/root/check_db_strat.py', 'w') as f:
        f.write(script)
    sftp.close()
    
    stdin, stdout, stderr = ssh.exec_command("/root/backend/venv/bin/python /root/check_db_strat.py")
    print(stdout.read().decode('utf-8'))
    
    ssh.close()
except Exception as e:
    print(f"Error: {e}")
