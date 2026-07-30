import paramiko
import time

IP = '206.189.129.232'
USER = 'root'
PASS = 'MyroomNo.is133g'

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(IP, username=USER, password=PASS, timeout=10)
    
    # Force delete and start
    print("Deleting and restarting algotrade-api correctly...")
    ssh.exec_command("cd /root/backend && pm2 delete algotrade-api")
    time.sleep(2)
    ssh.exec_command("cd /root/backend && pm2 start ecosystem.config.js --only algotrade-api")
    time.sleep(3)
    
    # Check logs
    stdin, stdout, stderr = ssh.exec_command("cat /root/.pm2/logs/algotrade-api-error.log | tail -n 10")
    print("ERRORS:")
    print(stdout.read().decode())
    
    stdin, stdout, stderr = ssh.exec_command("cat /root/.pm2/logs/algotrade-api-out.log | tail -n 10")
    print("OUTPUTS:")
    print(stdout.read().decode())
    
    ssh.close()
except Exception as e:
    print(f"Error: {e}")
