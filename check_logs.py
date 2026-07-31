import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('206.189.129.232', username='root', password='MyroomNo.is133g')

stdin, stdout, stderr = ssh.exec_command("cat /root/.pm2/logs/engine-a-technical-out.log | grep -i 'MetaAllocator'")
print(stdout.read().decode())
ssh.close()
