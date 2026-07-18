import paramiko

remote_host = '206.189.129.232'
remote_user = 'root'
password = 'MyroomNo.is133g'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    print(f"Connecting to {remote_host}...")
    ssh.connect(remote_host, username=remote_user, password=password)
    
    cmd = "pm2 status && echo '--- POSITIONS ---' && sqlite3 /root/backend/trading_system.db 'SELECT * FROM paper_positions;' && echo '--- TRADES ---' && sqlite3 /root/backend/trading_system.db 'SELECT * FROM paper_trades ORDER BY id DESC LIMIT 5;'"
    stdin, stdout, stderr = ssh.exec_command(cmd)
    
    out = stdout.read().decode('utf-8', errors='ignore')
    with open('engine_status.log', 'w', encoding='utf-8') as f:
        f.write(out)
        
    print("Logs saved to engine_status.log!")
    
except Exception as e:
    print(f"Error: {e}")
finally:
    ssh.close()
