import paramiko

IP = '206.189.129.232'
USER = 'root'
PASS = 'MyroomNo.is133g'

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(IP, username=USER, password=PASS, timeout=10)
    
    print(f"--- Open Positions ---")
    query = "SELECT id, symbol, strategy_id, entry_time, qty, entry_price FROM paper_positions;"
    stdin, stdout, stderr = ssh.exec_command(f"sqlite3 /root/backend/trading_system.db -header -column \"{query}\"")
    print(stdout.read().decode().strip())
        
    print("\n--- Recent Logs (live_trader) ---")
    stdin, stdout, stderr = ssh.exec_command("tail -n 20 /root/.pm2/logs/engine-a-technical-out.log")
    print(stdout.read().decode().strip())
    
    print("\n--- Recent Logs (engine errors) ---")
    stdin, stdout, stderr = ssh.exec_command("tail -n 20 /root/.pm2/logs/engine-a-technical-error.log")
    print(stdout.read().decode().strip())
    
    ssh.close()
except Exception as e:
    print(f"Error connecting: {e}")
