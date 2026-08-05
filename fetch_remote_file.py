import paramiko

IP = '206.189.129.232'
USER = 'root'
PASS = 'MyroomNo.is133g'

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(IP, username=USER, password=PASS, timeout=10)
    
    sftp = ssh.open_sftp()
    with sftp.open('/root/backend/feature_engine.py', 'r') as f:
        content = f.read().decode('utf-8')
        print(content[:1500])
    sftp.close()
    ssh.close()
except Exception as e:
    print(f"Error: {e}")
