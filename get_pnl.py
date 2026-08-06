import paramiko

IP = '206.189.129.232'
USER = 'root'
PASS = 'MyroomNo.is133g'

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(IP, username=USER, password=PASS, timeout=10)
    
    print(f"--- CLOSED TRADES (paper_trades) ---")
    query = "SELECT id, symbol, side, qty, entry_price, exit_price, pnl, exit_time FROM paper_trades ORDER BY id DESC LIMIT 5;"
    stdin, stdout, stderr = ssh.exec_command(f"sqlite3 /root/backend/trading_system.db -header -column \\\"{query}\\\"")
    print(stdout.read().decode().strip())
    print(f"\\n--- OPEN POSITIONS (paper_positions) ---")
    query2 = "SELECT id, symbol, qty, entry_price, entry_time FROM paper_positions ORDER BY id DESC LIMIT 5;"
    stdin, stdout, stderr = ssh.exec_command(f"sqlite3 /root/backend/trading_system.db -header -column \\\"{query2}\\\"")
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
