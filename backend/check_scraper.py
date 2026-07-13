import paramiko

remote_host = '206.189.129.232'
remote_user = 'root'
password = 'MyroomNo.is133g'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    ssh.connect(remote_host, username=remote_user, password=password)
    
    cmd = "echo '--- ERROR LOG ---' && cat ~/.pm2/logs/ultimate-scraper-error.log | tail -n 20"
    stdin, stdout, stderr = ssh.exec_command(cmd)
    
    print(stdout.read().decode('utf-8', errors='ignore'))
    
except Exception as e:
    print(f"Error: {e}")
finally:
    ssh.close()
