import paramiko

remote_host = '206.189.129.232'
remote_user = 'root'
password = 'MyroomNo.is133g'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    print(f"Connecting to {remote_host}...")
    ssh.connect(remote_host, username=remote_user, password=password)
    
    commands = [
        "cd /root/backend && pm2 delete training_monitor || true",
        "cd /root/backend && pm2 start ./venv/bin/python --name training_monitor -- -m streamlit run training_monitor.py --server.port 8501 --server.address 0.0.0.0",
        "cd /root/backend && pm2 save"
    ]
    
    for cmd in commands:
        print(f"Executing: {cmd}")
        stdin, stdout, stderr = ssh.exec_command(cmd)
        
        # Read but don't print complex characters to avoid Windows encoding crashes
        out = stdout.read()
        err = stderr.read()
        
    print("Streamlit has been successfully started with the correct Python interpreter!")
    
except Exception as e:
    print(f"Error: {e}")
finally:
    ssh.close()
