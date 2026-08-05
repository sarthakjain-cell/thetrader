import paramiko

IP = '206.189.129.232'
USER = 'root'
PASS = 'MyroomNo.is133g'

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(IP, username=USER, password=PASS, timeout=10)
    
    script = """
import sys
sys.path.append('/root/backend')
import pandas as pd
from feature_engine import compute_features
from strategy_001_orb import Strategy001ORB

df = pd.DataFrame({
    'Datetime': [pd.Timestamp('2026-08-05 09:15:00')],
    'Symbol': ['TCS.NS'],
    'Open': [2450],
    'High': [2460],
    'Low': [2440],
    'Close': [2456.3],
    'Volume': [1000]
})

df_features = compute_features(df)
strat = Strategy001ORB()
strat.params = strat.get_default_parameters()
current_bar = df_features.iloc[-1]
context = {'ai_forecasts': {'TCS.NS': 0.8}, 'sentiment': {}}
res = strat.evaluate('TCS.NS', current_bar, context)

print("Strategy Evaluation:", res)
"""
    sftp = ssh.open_sftp()
    with sftp.file('/root/test_strategy.py', 'w') as f:
        f.write(script)
    sftp.close()
    
    stdin, stdout, stderr = ssh.exec_command("/root/backend/venv/bin/python /root/test_strategy.py")
    print(stdout.read().decode('utf-8'))
    print("STDERR:", stderr.read().decode('utf-8'))
    
    ssh.close()
except Exception as e:
    print(f"Error: {e}")
