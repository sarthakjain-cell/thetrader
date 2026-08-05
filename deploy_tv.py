import paramiko
import os

IP = '206.189.129.232'
USER = 'root'
PASS = 'MyroomNo.is133g'

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(IP, username=USER, password=PASS, timeout=10)
    
    print("Installing tvDatafeed in venv...")
    stdin, stdout, stderr = ssh.exec_command("/root/backend/venv/bin/pip install --upgrade --no-cache-dir git+https://github.com/rongardF/tvdatafeed.git")
    stdout.read() # Wait for install
    
    sftp = ssh.open_sftp()
    
    print("Uploading data_provider.py...")
    local_data_provider = os.path.join("backend", "data_provider.py")
    sftp.put(local_data_provider, '/root/backend/data_provider.py')
    
    print("Uploading live_trader.py...")
    local_live_trader = os.path.join("backend", "live_trader.py")
    sftp.put(local_live_trader, '/root/backend/live_trader.py')
    
    print("Uploading feature_engine.py...")
    local_feature = os.path.join("backend", "feature_engine.py")
    sftp.put(local_feature, '/root/backend/feature_engine.py')
    
    sftp.close()
    
    print("Restarting engine...")
    stdin, stdout, stderr = ssh.exec_command("pm2 restart engine-a-technical")
    print(stdout.read().decode())
    
    ssh.close()
    print("Deployment successful! TradingView is now live.")
except Exception as e:
    print(f"Error: {e}")
