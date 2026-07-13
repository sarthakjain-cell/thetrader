import paramiko
import json

remote_host = '206.189.129.232'
remote_user = 'root'
password = 'MyroomNo.is133g'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    ssh.connect(remote_host, username=remote_user, password=password)
    
    stdin, stdout, stderr = ssh.exec_command('curl -s http://localhost:8000/api/poll')
    out = stdout.read().decode('utf-8')
    data = json.loads(out)
    
    print("Strategies returned from API:")
    print(json.dumps(data.get('strategies', []), indent=2))
    
except Exception as e:
    print(f"Error: {e}")
finally:
    ssh.close()
