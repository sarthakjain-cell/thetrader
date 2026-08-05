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
    print("Uploading backend/model_trainer.py...")
    scp.put('backend/model_trainer.py', remote_path='/root/backend/model_trainer.py')
    print("Uploading backend/engine_b_advisor.py...")
    scp.put('backend/engine_b_advisor.py', remote_path='/root/backend/engine_b_advisor.py')

print("Restarting ai-brain-daemon & engine-b-sentiment via PM2...")
stdin, stdout, stderr = ssh.exec_command("pm2 restart ai-brain-daemon engine-b-sentiment", get_pty=True)
stdout.read() # wait

ssh.close()
print("Done!")
