import paramiko

IP = '206.189.129.232'
USER = 'root'
PASS = 'MyroomNo.is133g'

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(IP, username=USER, password=PASS, timeout=10)
    
    # Enable WAL mode and set busy_timeout
    cmd = 'cd /root/backend && sqlite3 trading_system.db "PRAGMA journal_mode=WAL; PRAGMA busy_timeout=15000;"'
    stdin, stdout, stderr = ssh.exec_command(cmd)
    
    print("WAL OUTPUT:", stdout.read().decode())
    print("WAL ERRORS:", stderr.read().decode())
    
    ssh.close()
    print("WAL Mode enabled!")
except Exception as e:
    print(f"Error: {e}")
