import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("206.189.129.232", username="root", password="MyroomNo.is133g")

cleanup_script = """
import sqlite3
conn = sqlite3.connect('/root/backend/trading_system.db')
c = conn.cursor()
c.execute('DELETE FROM market_signals')
c.execute('DELETE FROM paper_trades WHERE notes LIKE "%Q1 results%"')
conn.commit()
conn.close()
print("Mock data cleared on server.")
"""

sftp = ssh.open_sftp()
with sftp.open("/root/backend/cleanup.py", "w") as f:
    f.write(cleanup_script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("cd /root/backend && source venv/bin/activate && python cleanup.py")
print("STDOUT:")
for line in stdout: print(line.strip().encode('ascii', 'ignore').decode('ascii'))
print("STDERR:")
for line in stderr: print(line.strip().encode('ascii', 'ignore').decode('ascii'))
ssh.close()
