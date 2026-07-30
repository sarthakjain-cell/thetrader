import paramiko
import os
import sys

IP = '206.189.129.232'
USER = 'root'
PASS = 'MyroomNo.is133g'

print(f"Connecting to {IP} for UI/UX Overhaul Deployment...")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    ssh.connect(IP, username=USER, password=PASS, timeout=10)
    
    # 1. Clear old frontend
    ssh.exec_command("rm -rf /root/backend/frontend_out/*")
    
    sftp = ssh.open_sftp()
    
    # 2. Upload API
    print("Uploading updated api.py...")
    sftp.put(os.path.join("backend", "api.py"), "/root/backend/api.py")
    
    # 3. Upload built frontend
    print("Uploading compiled Next.js static export...")
    local_dir = r"c:\Users\sjain\OneDrive\Desktop\algotrade-ai\frontend\out"
    remote_dir = "/root/backend/frontend_out"
    
    def put_dir(l_dir, r_dir):
        try:
            sftp.mkdir(r_dir)
        except Exception:
            pass
        for item in os.listdir(l_dir):
            l_item = os.path.join(l_dir, item)
            r_item = r_dir + "/" + item
            if os.path.isdir(l_item):
                put_dir(l_item, r_item)
            else:
                sftp.put(l_item, r_item)

    if os.path.exists(local_dir):
        put_dir(local_dir, remote_dir)
    else:
        print("Error: /frontend/out does not exist. Did the build fail?")
        sys.exit(1)
        
    sftp.close()
    
    # 4. Restart API
    print("Restarting API via PM2...")
    stdin, stdout, stderr = ssh.exec_command("cd /root/backend && pm2 restart algotrade-api")
    out = stdout.read().decode('utf-8', errors='replace')
    
    ssh.close()
    print("Deployment successful! The Command Center is live.")
    
except Exception as e:
    print(f"Failed to deploy: {e}")
    sys.exit(1)
