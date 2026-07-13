import paramiko
import os

remote_host = '206.189.129.232'
remote_user = 'root'
password = 'MyroomNo.is133g'
remote_base_dir = '/root/backend'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    print(f"Connecting to {remote_host}...")
    ssh.connect(remote_host, username=remote_user, password=password)
    sftp = ssh.open_sftp()
    
    local_path = os.path.join(os.getcwd(), 'api.py')
    remote_path = f"{remote_base_dir}/api.py"
    
    print(f"Uploading fixed api.py...")
    sftp.put(local_path, remote_path)
    sftp.close()
    
    print("Restarting 'algotrade-api'...")
    stdin, stdout, stderr = ssh.exec_command('cd /root/backend && pm2 restart algotrade-api')
    print(stdout.read().decode('utf-8', errors='ignore'))
    
    print("Fix deployed successfully!")
    
except Exception as e:
    print(f"Deployment failed: {e}")
finally:
    ssh.close()
