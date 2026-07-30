import paramiko

IP = '206.189.129.232'
USER = 'root'
PASS = 'MyroomNo.is133g'

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(IP, username=USER, password=PASS, timeout=10)
    
    stdin, stdout, stderr = ssh.exec_command("cat /root/.pm2/logs/algotrade-api-error.log | tail -n 10")
    errs = stdout.read().decode('utf-8', errors='ignore')
    
    stdin, stdout, stderr = ssh.exec_command("cat /root/.pm2/logs/algotrade-api-out.log | tail -n 5")
    outs = stdout.read().decode('utf-8', errors='ignore')
    
    print("ERRORS:")
    print(errs)
    print("OUTPUTS:")
    print(outs)
    
    ssh.close()
except Exception as e:
    print(f"Error: {e}")
