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
from data_provider import TradingViewProvider

provider = TradingViewProvider()
data = provider.get_today_data(['TCS.NS'])

df = data.get('TCS.NS')
if df is not None:
    print(f"Number of bars returned for today: {len(df)}")
    print(df.head())
    print(df.tail())
else:
    print("No data returned")
"""
    sftp = ssh.open_sftp()
    with sftp.file('/root/test_tv_data.py', 'w') as f:
        f.write(script)
    sftp.close()
    
    stdin, stdout, stderr = ssh.exec_command("/root/backend/venv/bin/python /root/test_tv_data.py")
    print(stdout.read().decode('utf-8'))
    print("STDERR:", stderr.read().decode('utf-8'))
    
    ssh.close()
except Exception as e:
    print(f"Error: {e}")
