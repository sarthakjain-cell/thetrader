import paramiko
import sys

IP = "206.189.129.232"
USER = "root"
PASS = "MyroomNo.is133g"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(IP, username=USER, password=PASS, timeout=10)

stdin, stdout, stderr = ssh.exec_command("pm2 status", get_pty=True)
print(stdout.read().decode(errors='ignore'))
ssh.close()
