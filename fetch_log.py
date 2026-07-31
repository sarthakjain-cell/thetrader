import paramiko

IP = '206.189.129.232'
USER = 'root'
PASS = 'MyroomNo.is133g'

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(IP, username=USER, password=PASS, timeout=10)
    
    stdin, stdout, stderr = ssh.exec_command("pm2 list")
    pm2_list = stdout.read().decode('utf-8', errors='ignore')
    
    stdin, stdout, stderr = ssh.exec_command("pm2 logs --lines 15 --nostream")
    pm2_logs = stdout.read().decode('utf-8', errors='ignore')
    
    with open('temp_log.txt', 'w', encoding='utf-8') as f:
        f.write("=== PM2 STATUS ===\n")
        f.write(pm2_list)
        f.write("\n=== RECENT PM2 LOGS ===\n")
        f.write(pm2_logs)
        
    print("Logs written to temp_log.txt")
    
    ssh.close()
except Exception as e:
    print(f"Error: {e}")
