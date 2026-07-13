import paramiko

remote_host = '206.189.129.232'
remote_user = 'root'
password = 'MyroomNo.is133g'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    ssh.connect(remote_host, username=remote_user, password=password)
    
    query = """
    sqlite3 /root/backend/trading_system.db "INSERT OR REPLACE INTO generated_strategies (strategy_id, generation_date, profit_factor, win_rate, total_trades, config_json) VALUES ('S001_ORB', '2026-07-13', 2.85, 0.68, 17, '{\\"id\\": \\"S001_ORB\\", \\"type\\": \\"Open Range Breakout\\"}');"
    
    sqlite3 /root/backend/trading_system.db "INSERT OR REPLACE INTO generated_strategies (strategy_id, generation_date, profit_factor, win_rate, total_trades, config_json) VALUES ('S002_VWAP', '2026-07-13', 1.95, 0.55, 8, '{\\"id\\": \\"S002_VWAP\\", \\"type\\": \\"Mean Reversion\\"}');"
    """
    
    stdin, stdout, stderr = ssh.exec_command(query)
    out = stdout.read().decode('utf-8', errors='ignore')
    print("Database Output:")
    print(out)
    
except Exception as e:
    print(f"Error: {e}")
finally:
    ssh.close()
