import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('206.189.129.232', username='root', password='MyroomNo.is133g')
script = """import sqlite3
conn = sqlite3.connect('/root/backend/trading_system.db')
cursor = conn.cursor()
cursor.execute("PRAGMA table_info(market_data_1d)")
print("Columns:", [row[1] for row in cursor.fetchall()])
"""

# write script to remote
sftp = ssh.open_sftp()
with sftp.file('/root/backend/check.py', 'w') as f:
    f.write(script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('/root/backend/venv/bin/python /root/backend/check.py')
print('STDOUT:\n', stdout.read().decode())
print('STDERR:\n', stderr.read().decode())
ssh.close()
