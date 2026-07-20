import paramiko
from scp import SCPClient
import os

IP = "206.189.129.232"
USER = "root"
PASS = "MyroomNo.is133g"

print(f"Connecting to {IP}...")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(IP, username=USER, password=PASS, timeout=10)

with SCPClient(ssh.get_transport()) as scp:
    print("Uploading paper_trader.py...")
    scp.put('backend/paper_trader.py', remote_path='/root/backend/paper_trader.py')

print("Restarting live_trader via PM2...")
stdin, stdout, stderr = ssh.exec_command("cd /root/backend && source venv/bin/activate && pm2 restart live_trader --update-env", get_pty=True)
print(stdout.read().decode(errors='ignore'))
print(stderr.read().decode(errors='ignore'))

ssh.close()
print("Done!")
