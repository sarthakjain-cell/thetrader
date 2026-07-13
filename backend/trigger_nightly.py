import paramiko
import re

remote_host = '206.189.129.232'
remote_user = 'root'
password = 'MyroomNo.is133g'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

def clean_output(output):
    return re.sub(r'[\x00-\x1F\x7F-\x9F]', '', output)

try:
    ssh.connect(remote_host, username=remote_user, password=password)
    
    print("Triggering daily_reporter.py...")
    stdin, stdout, stderr = ssh.exec_command('cd /root/backend && ./venv/bin/python daily_reporter.py')
    print(clean_output(stdout.read().decode('utf-8', errors='ignore')))
    
    print("Triggering nightly_factory.py...")
    # This might take a bit longer if it connects to Gemini to synthesize strategies
    stdin, stdout, stderr = ssh.exec_command('cd /root/backend && ./venv/bin/python nightly_factory.py')
    print(clean_output(stdout.read().decode('utf-8', errors='ignore')))
    
    # Restart the api so it fetches the new strategies
    ssh.exec_command('pm2 restart algotrade-api')
    print("Restarted algotrade-api to load new strategies.")
    
except Exception as e:
    print(f"Error: {e}")
finally:
    ssh.close()
