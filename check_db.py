import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("206.189.129.232", username="root", password="MyroomNo.is133g")

commands = [
    "sqlite3 /root/backend/trading_system.db 'SELECT * FROM research_tips;'",
    "sqlite3 /root/backend/trading_system.db 'SELECT date FROM research_tips LIMIT 5;'",
    "date"
]

for cmd in commands:
    print(f"--- {cmd} ---")
    stdin, stdout, stderr = ssh.exec_command(cmd)
    for line in stdout: print(line.strip())
    for line in stderr: print(line.strip())

ssh.close()
