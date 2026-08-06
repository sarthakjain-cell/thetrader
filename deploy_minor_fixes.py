import paramiko
from scp import SCPClient

IP = "206.189.129.232"
USER = "root"
PASS = "MyroomNo.is133g"

print(f"Connecting to {IP}...")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(IP, username=USER, password=PASS, timeout=10)

with SCPClient(ssh.get_transport()) as scp:
    print("Uploading backend/strategy_001_orb.py...")
    scp.put('backend/strategy_001_orb.py', remote_path='/root/backend/strategy_001_orb.py')
    print("Uploading backend/strategy_002_vwap.py...")
    scp.put('backend/strategy_002_vwap.py', remote_path='/root/backend/strategy_002_vwap.py')

print("Restarting engine-a-technical via PM2...")
stdin, stdout, stderr = ssh.exec_command("pm2 restart engine-a-technical", get_pty=True)
stdout.read() # wait

ssh.close()
print("Done!")
