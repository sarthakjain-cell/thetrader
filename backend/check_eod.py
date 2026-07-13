import paramiko
import json

remote_host = '206.189.129.232'
remote_user = 'root'
password = 'MyroomNo.is133g'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    ssh.connect(remote_host, username=remote_user, password=password)
    
    query = """
    echo "--- TODAY'S TRADES ---"
    sqlite3 /root/backend/trading_system.db "SELECT count(*), sum(pnl) FROM paper_trades WHERE date(exit_time) = date('now', 'localtime');"
    
    echo "--- DAILY SUMMARY TABLE ---"
    sqlite3 /root/backend/trading_system.db "SELECT * FROM daily_summary ORDER BY date DESC LIMIT 5;"
    
    echo "--- BEST TRADE ---"
    sqlite3 /root/backend/trading_system.db "SELECT symbol, pnl, strategy_id FROM paper_trades WHERE date(exit_time) = date('now', 'localtime') ORDER BY pnl DESC LIMIT 1;"
    
    echo "--- WORST TRADE ---"
    sqlite3 /root/backend/trading_system.db "SELECT symbol, pnl, strategy_id FROM paper_trades WHERE date(exit_time) = date('now', 'localtime') ORDER BY pnl ASC LIMIT 1;"
    """
    
    stdin, stdout, stderr = ssh.exec_command(query)
    out = stdout.read().decode('utf-8', errors='ignore')
    print(out)
    
except Exception as e:
    print(f"Error: {e}")
finally:
    ssh.close()
