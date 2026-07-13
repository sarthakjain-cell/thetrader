import paramiko

remote_host = '206.189.129.232'
remote_user = 'root'
password = 'MyroomNo.is133g'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    ssh.connect(remote_host, username=remote_user, password=password)
    
    query = """
    sqlite3 /root/backend/trading_system.db "SELECT count(*) FROM generated_strategies;"
    sqlite3 /root/backend/trading_system.db "SELECT strategy_id FROM generated_strategies;"
    """
    
    stdin, stdout, stderr = ssh.exec_command(query)
    out = stdout.read().decode('utf-8', errors='ignore')
    print("Database Output:")
    print(out)
    
except Exception as e:
    print(f"Error: {e}")
finally:
    ssh.close()
