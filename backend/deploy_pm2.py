import paramiko
import os

host = '206.189.129.232'
user = 'root'
password = 'MyroomNo.is133g'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    ssh.connect(host, username=user, password=password)
    sftp = ssh.open_sftp()
    
    local_path = os.path.join(os.getcwd(), 'ecosystem.config.js')
    remote_path = "/root/backend/ecosystem.config.js"
    sftp.put(local_path, remote_path)
    sftp.close()
    
    # Run pm2 start and save
    stdin, stdout, stderr = ssh.exec_command('cd /root/backend && pm2 start ecosystem.config.js && pm2 save')
    print("Restarted PM2 with new config")
except Exception as e:
    print(f"Deployment failed: {e}")
finally:
    ssh.close()
