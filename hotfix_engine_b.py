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
    print("Uploading engine_b_advisor.py...")
    scp.put('backend/engine_b_advisor.py', remote_path='/root/backend/engine_b_advisor.py')

print("Restarting engine-b-sentiment via PM2...")
stdin, stdout, stderr = ssh.exec_command("pm2 restart engine-b-sentiment", get_pty=True)
print(stdout.read().decode(errors='ignore'))
print(stderr.read().decode(errors='ignore'))

ssh.close()
print("Done!")
