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
conn = sqlite3.connect('/root/backend/trading_system.db')
cursor = conn.cursor()

print("Clearing today's rogue trades...")
cursor.execute("DELETE FROM paper_trades WHERE date(entry_time) = '2026-08-05'")
print(f"Deleted {cursor.rowcount} closed trades.")

cursor.execute("DELETE FROM paper_positions WHERE date(entry_time) = '2026-08-05'")
print(f"Deleted {cursor.rowcount} open positions.")

# Also remove dynamic strategies to be safe
cursor.execute("DELETE FROM generated_strategies")
print(f"Deleted {cursor.rowcount} dynamic strategies.")

conn.commit()
conn.close()
"""
    sftp = ssh.open_sftp()
    with sftp.file('/root/clear_rogue.py', 'w') as f:
        f.write(script)
    sftp.close()
    
    stdin, stdout, stderr = ssh.exec_command("/root/backend/venv/bin/python /root/clear_rogue.py")
    print(stdout.read().decode('utf-8'))
    
    ssh.close()
except Exception as e:
    print(f"Error: {e}")
