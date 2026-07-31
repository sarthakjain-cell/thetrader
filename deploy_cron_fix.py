import paramiko
import os

IP = '206.189.129.232'
USER = 'root'
PASS = 'MyroomNo.is133g'

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(IP, username=USER, password=PASS, timeout=10)
    
    sftp = ssh.open_sftp()
    
    files_to_upload = [
        ("backend/daily_reporter.py", "/root/backend/daily_reporter.py"),
        ("backend/feature_engine.py", "/root/backend/feature_engine.py")
    ]
    
    for local, remote in files_to_upload:
        sftp.put(local, remote)
        print(f"Uploaded {local} to {remote}")
        
    sftp.close()
    ssh.close()
    print("Fixes deployed successfully!")
except Exception as e:
    print(f"Error: {e}")
