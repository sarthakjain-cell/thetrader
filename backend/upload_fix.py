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
    
    local_path = os.path.join(os.getcwd(), 'training_monitor.py')
    remote_path = f"{remote_base_dir}/training_monitor.py"
    
    print(f"Uploading fixed training_monitor.py...")
    sftp.put(local_path, remote_path)
    sftp.close()
    
    print("Restarting 'training_monitor'...")
    stdin, stdout, stderr = ssh.exec_command('cd /root/backend && pm2 restart training_monitor')
    out = stdout.read()
    
    print("Fix deployed successfully!")
    
except Exception as e:
    print(f"Deployment failed: {e}")
finally:
    ssh.close()
