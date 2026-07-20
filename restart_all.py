import paramiko

IP = "206.189.129.232"
USER = "root"
PASS = "MyroomNo.is133g"

print(f"Connecting to {IP}...")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(IP, username=USER, password=PASS, timeout=10)

print("Restarting ALL PM2 processes to load new API key...")
stdin, stdout, stderr = ssh.exec_command("cd /root/backend && source venv/bin/activate && pm2 restart all --update-env", get_pty=True)
print(stdout.read().decode(errors='ignore').encode('ascii', errors='ignore').decode())

ssh.close()
print("Done!")
