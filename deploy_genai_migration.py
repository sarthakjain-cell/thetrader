import paramiko
from scp import SCPClient

IP = "206.189.129.232"
USER = "root"
PASS = "MyroomNo.is133g"

print(f"Connecting to {IP}...")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(IP, username=USER, password=PASS, timeout=10)

print("Installing google-genai on the VPS...")
stdin, stdout, stderr = ssh.exec_command("cd /root/backend && source venv/bin/activate && pip install google-genai", get_pty=True)
stdout.read() # wait for completion

with SCPClient(ssh.get_transport()) as scp:
    print("Uploading backend/engine_b_advisor.py...")
    scp.put('backend/engine_b_advisor.py', remote_path='/root/backend/engine_b_advisor.py')
    print("Uploading backend/api.py...")
    scp.put('backend/api.py', remote_path='/root/backend/api.py')

print("Restarting engine-b-sentiment & algotrade-api via PM2...")
stdin, stdout, stderr = ssh.exec_command("pm2 restart engine-b-sentiment algotrade-api", get_pty=True)
stdout.read() # wait for completion

ssh.close()
print("Done!")
