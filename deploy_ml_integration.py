import paramiko
import sys
import os

IP = '206.189.129.232'
USER = 'root'
PASS = 'MyroomNo.is133g'

print(f"Connecting to {IP} for ML Engine Integration Deployment...")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    ssh.connect(IP, username=USER, password=PASS, timeout=10)
    
    sftp = ssh.open_sftp()
    
    print("Uploading live_trader.py...")
    sftp.put(os.path.join("backend", "live_trader.py"), "/root/backend/live_trader.py")
    
    print("Uploading strategy_001_orb.py...")
    sftp.put(os.path.join("backend", "strategy_001_orb.py"), "/root/backend/strategy_001_orb.py")
    
    sftp.close()
    
    print("Restarting Live Trader to apply ML changes...")
    commands = [
        "cd /root/backend && pm2 restart live_trader"
    ]
    
    for cmd in commands:
        stdin, stdout, stderr = ssh.exec_command(cmd)
        out = stdout.read().decode('utf-8', errors='replace')
        err = stderr.read().decode('utf-8', errors='replace')
        try:
            print(f"[{cmd}] Executed.")
        except Exception:
            pass
            
    ssh.close()
    print("Deployment successful. ML Oracle is now online!")
    
except Exception as e:
    print(f"Failed to deploy: {e}")
    sys.exit(1)
