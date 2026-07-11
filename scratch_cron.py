import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("206.189.129.232", username="root", password="MyroomNo.is133g")

cmd = '(crontab -l 2>/dev/null | grep -v night_researcher; echo "30 10 * * 1-5 /root/backend/venv/bin/python /root/backend/night_researcher.py") | crontab -'
ssh.exec_command(cmd)
ssh.close()
print("Cron set")
