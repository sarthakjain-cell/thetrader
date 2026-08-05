import paramiko
from scp import SCPClient

IP = "206.189.129.232"
USER = "root"
PASS = "MyroomNo.is133g"

print(f"Connecting to {IP}...")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(IP, username=USER, password=PASS, timeout=10)

print("Installing tenacity on the VPS...")
stdin, stdout, stderr = ssh.exec_command("cd /root/backend && source venv/bin/activate && pip install tenacity", get_pty=True)
stdout.read() # wait

with SCPClient(ssh.get_transport()) as scp:
    print("Uploading backend/ecosystem.config.js...")
    scp.put('backend/ecosystem.config.js', remote_path='/root/backend/ecosystem.config.js')
    print("Uploading backend/ai_brain_daemon.py...")
    scp.put('backend/ai_brain_daemon.py', remote_path='/root/backend/ai_brain_daemon.py')
    print("Uploading backend/data_provider.py...")
    scp.put('backend/data_provider.py', remote_path='/root/backend/data_provider.py')

print("Restarting ecosystem via PM2...")
stdin, stdout, stderr = ssh.exec_command("cd /root/backend && pm2 reload ecosystem.config.js --update-env", get_pty=True)
stdout.read() # wait

ssh.close()
print("Done!")
