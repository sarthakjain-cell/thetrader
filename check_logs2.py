import paramiko

IP = '206.189.129.232'
USER = 'root'
PASS = 'MyroomNo.is133g'

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(IP, username=USER, password=PASS, timeout=10)
    
    stdin, stdout, stderr = ssh.exec_command("grep '03:45:' /root/.pm2/logs/engine-a-technical-out.log | tail -n 30")
    print("--- 03:45 (09:15 IST) LOGS ---")
    print(stdout.read().decode('utf-8'))
    
    ssh.close()
except Exception as e:
    print(f"Error: {e}")
