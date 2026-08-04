import paramiko
import time

IP = '206.189.129.232'
USER = 'root'
PASS = 'MyroomNo.is133g'

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(IP, username=USER, password=PASS, timeout=10)
    
    print("Installing tvDatafeed...")
    stdin, stdout, stderr = ssh.exec_command("/root/backend/venv/bin/pip install --upgrade --no-cache-dir git+https://github.com/rongardF/tvdatafeed.git")
    stdout.read() # Wait for install
    
    test_script = """
from tvDatafeed import TvDatafeed, Interval
import logging

logging.basicConfig(level=logging.DEBUG)
try:
    tv = TvDatafeed()
    df = tv.get_hist(symbol='RELIANCE', exchange='NSE', interval=Interval.in_5_minute, n_bars=10)
    print(df)
except Exception as e:
    print(f"Error: {e}")
"""
    sftp = ssh.open_sftp()
    with sftp.file('/root/test_tv.py', 'w') as f:
        f.write(test_script)
    sftp.close()
    
    print("Running tvDatafeed test...")
    stdin, stdout, stderr = ssh.exec_command("/root/backend/venv/bin/python /root/test_tv.py")
    print(stdout.read().decode())
    print("Errors:", stderr.read().decode())
    
    ssh.close()
except Exception as e:
    print(f"Error: {e}")
