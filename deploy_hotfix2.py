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
    print("Uploading api.py...")
    scp.put('backend/api.py', remote_path='/root/backend/api.py')

print("Restarting algotrade-api via PM2...")
stdin, stdout, stderr = ssh.exec_command("cd /root/backend && source venv/bin/activate && pm2 restart algotrade-api --update-env", get_pty=True)
print(stdout.read().decode(errors='ignore'))
print(stderr.read().decode(errors='ignore'))

ssh.close()
print("Done!")
