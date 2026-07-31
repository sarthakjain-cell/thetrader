import paramiko
from datetime import datetime

IP = '206.189.129.232'
USER = 'root'
PASS = 'MyroomNo.is133g'

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(IP, username=USER, password=PASS, timeout=10)
    
    print(f"--- Checking Live Trades on {IP} ---")
    
    # 1. Check PM2 logs for any errors
    print("\n[Engine Status]")
    stdin, stdout, stderr = ssh.exec_command("pm2 jlist | grep -i engine")
    print(stdout.read().decode())
    
    # 2. Check Open Positions
    print("\n[Open Positions]")
    stdin, stdout, stderr = ssh.exec_command("sqlite3 /root/backend/trading_system.db -header -column 'SELECT id, symbol, strategy_id, entry_time, qty, entry_price FROM paper_positions;'")
    pos = stdout.read().decode().strip()
    if not pos:
        print("No open positions.")
    else:
        print(pos)
        
    # 3. Check Closed Trades Today
    today = datetime.now().strftime('%Y-%m-%d')
    print(f"\n[Closed Trades Today - {today}]")
    query = f"SELECT id, symbol, strategy_id, entry_time, exit_time, pnl, reason FROM paper_trades WHERE date(exit_time) = '{today}';"
    stdin, stdout, stderr = ssh.exec_command(f"sqlite3 /root/backend/trading_system.db -header -column \"{query}\"")
    trades = stdout.read().decode().strip()
    if not trades:
        print("No closed trades today.")
    else:
        print(trades)
        
    # 4. Check Recent Logs
    print("\n[Last 10 Lines of live_trader log]")
    stdin, stdout, stderr = ssh.exec_command("tail -n 10 /root/.pm2/logs/engine-a-technical-out.log")
    print(stdout.read().decode())
    
    ssh.close()
except Exception as e:
    print(f"Error connecting: {e}")
