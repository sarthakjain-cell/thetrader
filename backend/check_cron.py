import paramiko

remote_host = '206.189.129.232'
remote_user = 'root'
password = 'MyroomNo.is133g'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    ssh.connect(remote_host, username=remote_user, password=password)
    
    query = """
    echo "--- PM2 LIST ---"
    pm2 list
    
    echo "--- PM2 SHOW NIGHTLY ---"
    pm2 show algotrade-nightly
    
    echo "--- PM2 SHOW DAILY REPORTER ---"
    pm2 show daily-reporter
    """
    
    stdin, stdout, stderr = ssh.exec_command(query)
    out = stdout.read().decode('utf-8', errors='ignore')
    print(out)
    
except Exception as e:
    print(f"Error: {e}")
finally:
    ssh.close()
