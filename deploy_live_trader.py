import paramiko
import sys
import os

IP = '206.189.129.232'
USER = 'root'
PASS = 'MyroomNo.is133g'

print(f"Connecting to {IP}...")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    ssh.connect(IP, username=USER, password=PASS, timeout=10)
    
    # Upload live_trader.py
    print("Uploading live_trader.py...")
    sftp = ssh.open_sftp()
    local_path = os.path.join("backend", "live_trader.py")
    remote_path = "/root/backend/live_trader.py"
    sftp.put(local_path, remote_path)
    sftp.close()
    
    # Restart PM2
    print("Restarting live_trader via PM2...")
    stdin, stdout, stderr = ssh.exec_command("pm2 restart live_trader")
    
    # Decode with errors='replace' to avoid charmap UnicodeEncodeError on Windows
    out = stdout.read().decode('utf-8', errors='replace')
    err = stderr.read().decode('utf-8', errors='replace')
    print(out)
    if err:
        print("ERRORS:", err)
        
    ssh.close()
    print("Deployment successful.")
    
except Exception as e:
    print(f"Failed to deploy: {e}")
    sys.exit(1)
