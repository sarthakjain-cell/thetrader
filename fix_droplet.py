import paramiko
import os
import time

IP = '206.189.129.232'
USER = 'root'
PASS = 'MyroomNo.is133g'

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(IP, username=USER, password=PASS, timeout=10)
    
    # Upload latest requirements and ecosystem config
    sftp = ssh.open_sftp()
    
    local_req = os.path.join("backend", "requirements.txt")
    remote_req = "/root/backend/requirements.txt"
    sftp.put(local_req, remote_req)
    print(f"Uploaded {local_req} to {remote_req}")
    
    local_eco = os.path.join("backend", "ecosystem.config.js")
    remote_eco = "/root/backend/ecosystem.config.js"
    sftp.put(local_eco, remote_eco)
    print(f"Uploaded {local_eco} to {remote_eco}")
    
    # Let's also upload engine_b_advisor.py to make sure it's up to date
    local_eb = os.path.join("backend", "engine_b_advisor.py")
    remote_eb = "/root/backend/engine_b_advisor.py"
    sftp.put(local_eb, remote_eb)
    
    local_lt = os.path.join("backend", "live_trader.py")
    remote_lt = "/root/backend/live_trader.py"
    sftp.put(local_lt, remote_lt)
    
    sftp.close()
    
    # Run pip install
    print("Installing dependencies...")
    stdin, stdout, stderr = ssh.exec_command("cd /root/backend && /root/backend/venv/bin/python -m pip install -r requirements.txt")
    print("PIP STDOUT:", stdout.read().decode())
    err = stderr.read().decode()
    if err:
        print("PIP STDERR:", err)
    
    # Restart PM2 completely
    print("Restarting PM2 with new ecosystem config...")
    ssh.exec_command("pm2 delete all")
    time.sleep(2)
    stdin, stdout, stderr = ssh.exec_command("cd /root/backend && pm2 start ecosystem.config.js")
    print(stdout.read().decode())
    
    time.sleep(3)
    stdin, stdout, stderr = ssh.exec_command("pm2 list")
    print("FINAL PM2 STATUS:")
    print(stdout.read().decode('utf-8', errors='ignore'))
    
    ssh.close()
    print("Fix applied successfully!")
except Exception as e:
    print(f"Error: {e}")
