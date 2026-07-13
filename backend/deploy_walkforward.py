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
    
    local_path = os.path.join(os.getcwd(), 'walk_forward.py')
    remote_path = "/root/backend/walk_forward.py"
    sftp.put(local_path, remote_path)
    sftp.close()
    
    print("Uploaded walk_forward.py to VPS.")
except Exception as e:
    print(f"Deployment failed: {e}")
finally:
    ssh.close()
