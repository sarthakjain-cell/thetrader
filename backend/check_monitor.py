import paramiko

remote_host = '206.189.129.232'
remote_user = 'root'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    print(f"Connecting to {remote_host}...")
    ssh.connect(remote_host, username=remote_user)
    
    print("--- PM2 STATUS ---")
    stdin, stdout, stderr = ssh.exec_command('pm2 list')
    print(stdout.read().decode('utf-8', errors='ignore'))
    
    print("--- STREAMLIT ERROR LOG ---")
    stdin, stdout, stderr = ssh.exec_command('cat ~/.pm2/logs/training-monitor-error.log | tail -n 30')
    print(stdout.read().decode('utf-8', errors='ignore'))
    
    print("--- STREAMLIT OUT LOG ---")
    stdin, stdout, stderr = ssh.exec_command('cat ~/.pm2/logs/training-monitor-out.log | tail -n 30')
    print(stdout.read().decode('utf-8', errors='ignore'))
    
except Exception as e:
    print(f"Error: {e}")
finally:
    ssh.close()
