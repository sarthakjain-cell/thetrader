import paramiko

remote_host = '206.189.129.232'
remote_user = 'root'
password = 'MyroomNo.is133g'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    print(f"Connecting to {remote_host}...")
    ssh.connect(remote_host, username=remote_user, password=password)
    
    cmd = "cat ~/.pm2/logs/training-monitor-error.log | tail -n 100"
    stdin, stdout, stderr = ssh.exec_command(cmd)
    
    out = stdout.read().decode('utf-8', errors='ignore')
    with open('streamlit_error.log', 'w', encoding='utf-8') as f:
        f.write(out)
        
    print("Logs saved to streamlit_error.log!")
    
except Exception as e:
    print(f"Error: {e}")
finally:
    ssh.close()
