import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("206.189.129.232", username="root", password="MyroomNo.is133g")
stdin, stdout, stderr = ssh.exec_command("sqlite3 /root/backend/trading_system.db \"SELECT * FROM research_tips;\"")
print("STDOUT:")
for line in stdout:
    print(line.strip())
print("STDERR:")
for line in stderr:
    print(line.strip())
ssh.close()
