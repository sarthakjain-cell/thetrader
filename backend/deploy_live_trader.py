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
    
    # 1. Upload fixed live_trader.py
    local_path = os.path.join(os.getcwd(), 'live_trader.py')
    remote_path = f"{remote_base_dir}/live_trader.py"
    print(f"Uploading fixed live_trader.py...")
    sftp.put(local_path, remote_path)
    sftp.close()
    
    # 2. Execute PM2 and DB fixes
    commands = [
        "cd /root/backend && sqlite3 trading_system.db 'PRAGMA journal_mode=WAL; PRAGMA busy_timeout=5000;'",
        "cd /root/backend && pm2 delete engine-a-technical || true",
        "cd /root/backend && pm2 delete live_trader || true",
        "cd /root/backend && pm2 start ./venv/bin/python --name live_trader -- live_trader.py",
        "cd /root/backend && pm2 save"
    ]
    
    for cmd in commands:
        print(f"Executing: {cmd}")
        stdin, stdout, stderr = ssh.exec_command(cmd)
        out = stdout.read()
        
    print("Fixes deployed and live_trader successfully started!")
    
except Exception as e:
    print(f"Deployment failed: {e}")
finally:
    ssh.close()
