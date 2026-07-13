import paramiko

remote_host = '206.189.129.232'
remote_user = 'root'
password = 'MyroomNo.is133g'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    ssh.connect(remote_host, username=remote_user, password=password)
    
    stdin, stdout, stderr = ssh.exec_command('cd /root/backend && ./venv/bin/python nightly_factory.py')
    out = stdout.read().decode('utf-8', errors='ignore')
    err = stderr.read().decode('utf-8', errors='ignore')
    
    print("--- STDOUT ---")
    print(out)
    print("--- STDERR ---")
    print(err)
    
except Exception as e:
    print(f"Error: {e}")
finally:
    ssh.close()
