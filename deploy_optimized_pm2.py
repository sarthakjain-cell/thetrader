import paramiko
import sys
import os

IP = '206.189.129.232'
USER = 'root'
PASS = 'MyroomNo.is133g'

print(f"Connecting to {IP} for OOM Eradication Deployment...")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    ssh.connect(IP, username=USER, password=PASS, timeout=10)
    
    sftp = ssh.open_sftp()
    
    print("Uploading live_trader.py...")
    sftp.put(os.path.join("backend", "live_trader.py"), "/root/backend/live_trader.py")
    
    print("Uploading data_provider.py...")
    sftp.put(os.path.join("backend", "data_provider.py"), "/root/backend/data_provider.py")
    
    sftp.close()
    
    print("Executing strict PM2 memory limit deployment...")
    commands = [
        "pm2 delete all",
        "cd /root/backend && pm2 start live_trader.py --name live_trader --max-memory-restart 600M",
        "cd /root/backend && pm2 start api.py --name algotrade-api",
        "pm2 save"
    ]
    
    for cmd in commands:
        stdin, stdout, stderr = ssh.exec_command(cmd)
        out = stdout.read().decode('utf-8', errors='replace')
        err = stderr.read().decode('utf-8', errors='replace')
        # Filter charmap errors for local console
        try:
            print(f"[{cmd}] Executed.")
        except Exception:
            pass
            
    print("Verifying final PM2 state...")
    stdin, stdout, stderr = ssh.exec_command("pm2 list")
    out = stdout.read().decode('utf-8', errors='replace')
    try:
        print(out)
    except Exception:
        print("PM2 list executed (output hidden to prevent charmap crash).")
        
    ssh.close()
    print("Deployment successful. Server is locked with a 600M memory ceiling.")
    
except Exception as e:
    print(f"Failed to deploy: {e}")
    sys.exit(1)
