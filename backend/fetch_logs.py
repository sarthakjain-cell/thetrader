import paramiko

remote_host = '206.189.129.232'
remote_user = 'root'
password = 'MyroomNo.is133g'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    print(f"Connecting to {remote_host}...")
    ssh.connect(remote_host, username=remote_user, password=password)
    
    cmd = "echo '--- ENGINE A ERROR LOG ---' && cat ~/.pm2/logs/engine-a-technical-error.log | tail -n 20 && echo '--- ENGINE A OUT LOG ---' && cat ~/.pm2/logs/engine-a-technical-out.log | tail -n 20 && echo '--- DB CHECK ---' && sqlite3 /root/backend/trading_system.db 'SELECT count(*) FROM paper_trades;'"
    stdin, stdout, stderr = ssh.exec_command(cmd)
    
    out = stdout.read().decode('utf-8', errors='ignore')
    with open('engine_status.log', 'w', encoding='utf-8') as f:
        f.write(out)
        
    print("Logs saved to engine_status.log!")
    
except Exception as e:
    print(f"Error: {e}")
finally:
    ssh.close()
