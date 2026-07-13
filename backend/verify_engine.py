import paramiko
import time

remote_host = '206.189.129.232'
remote_user = 'root'
password = 'MyroomNo.is133g'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    ssh.connect(remote_host, username=remote_user, password=password)
    
    # Wait 10 seconds for it to process some ticks
    print("Waiting 10 seconds for engine to boot and run...")
    time.sleep(10)
    
    cmd = "echo '--- LIVE TRADER ERROR LOG ---' && cat ~/.pm2/logs/live-trader-error.log | tail -n 10 && echo '--- LIVE TRADER OUT LOG ---' && cat ~/.pm2/logs/live-trader-out.log | tail -n 10"
    stdin, stdout, stderr = ssh.exec_command(cmd)
    
    print(stdout.read().decode('utf-8', errors='ignore'))
    
except Exception as e:
    print(f"Error: {e}")
finally:
    ssh.close()
