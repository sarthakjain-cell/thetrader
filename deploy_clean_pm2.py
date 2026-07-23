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
    
    # Clean PM2 and Restart
    print("Executing PM2 wipe and clean start...")
    commands = [
        "pm2 delete all",
        "cd /root/backend && pm2 start live_trader.py --name live_trader",
        "cd /root/backend && pm2 start api.py --name algotrade-api",
        "pm2 save"
    ]
    
    for cmd in commands:
        stdin, stdout, stderr = ssh.exec_command(cmd)
        out = stdout.read().decode('utf-8', errors='replace')
        err = stderr.read().decode('utf-8', errors='replace')
        print(f"[{cmd}]\n{out}")
        if err:
            print(f"ERR: {err}")
            
    # Verify PM2 processes
    print("Verifying final PM2 state...")
    stdin, stdout, stderr = ssh.exec_command("pm2 list")
    out = stdout.read().decode('utf-8', errors='replace')
    print(out)
        
    ssh.close()
    print("Clean deployment successful.")
    
except Exception as e:
    print(f"Failed to deploy: {e}")
    sys.exit(1)
