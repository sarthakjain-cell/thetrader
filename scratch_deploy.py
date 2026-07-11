import paramiko
import os

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("206.189.129.232", username="root", password="MyroomNo.is133g")

sftp = ssh.open_sftp()

# 1. Upload backend files
local_backend = "c:\\Users\\sjain\\OneDrive\\Desktop\\algotrade-ai\\backend\\"
remote_backend = "/root/backend/"

files_to_upload = ['api.py', 'database.py', 'night_researcher.py']
for f in files_to_upload:
    print(f"Uploading {f}...")
    sftp.put(os.path.join(local_backend, f), os.path.join(remote_backend, f))

sftp.close()

# 2. Run database migration and restart API
commands = [
    "cd /root/backend && source venv/bin/activate && python database.py",
    "pm2 restart algotrade-api",
    # Setup cron job
    '(crontab -l 2>/dev/null | grep -v night_researcher; echo "30 10 * * 1-5 /root/backend/venv/bin/python /root/backend/night_researcher.py") | crontab -'
]

for cmd in commands:
    print(f"Executing: {cmd}")
    stdin, stdout, stderr = ssh.exec_command(cmd)
    for line in stdout: print(line.strip())
    for line in stderr: print(line.strip())

ssh.close()
print("Deployment complete!")
