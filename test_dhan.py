import paramiko
from datetime import datetime

IP = '206.189.129.232'
USER = 'root'
PASS = 'MyroomNo.is133g'

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(IP, username=USER, password=PASS, timeout=10)
    
    test_script = """
import sys
import pandas as pd
from datetime import datetime
import json

try:
    from dhanhq import dhanhq
    try:
        from dhanhq import DhanContext
        context = DhanContext("1112946078", "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJkaGFuIiwicGFydG5lcklkIjoiIiwiZXhwIjoxNzg1OTU3Nzk4LCJpYXQiOjE3ODU4NzEzOTgsInRva2VuQ29uc3VtZXJUeXBlIjoiU0VMRiIsIndlYmhvb2tVcmwiOiIiLCJkaGFuQ2xpZW50SWQiOiIxMTEyOTQ2MDc4In0.dm7OASjiBn1kefjv5BlrY_mU0yS5YQHS87M_Xf2H2z8a5JeFfwaQNsMPoRVBOIynpTezT1x2M-akJw5GPWeMuA")
        dhan = dhanhq(context)
    except ImportError:
        dhan = dhanhq("1112946078", "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJkaGFuIiwicGFydG5lcklkIjoiIiwiZXhwIjoxNzg1OTU3Nzk4LCJpYXQiOjE3ODU4NzEzOTgsInRva2VuQ29uc3VtZXJUeXBlIjoiU0VMRiIsIndlYmhvb2tVcmwiOiIiLCJkaGFuQ2xpZW50SWQiOiIxMTEyOTQ2MDc4In0.dm7OASjiBn1kefjv5BlrY_mU0yS5YQHS87M_Xf2H2z8a5JeFfwaQNsMPoRVBOIynpTezT1x2M-akJw5GPWeMuA")
    except Exception as e:
        print(f"Init Error: {e}")
        
    today = datetime.now().strftime('%Y-%m-%d')
    intraday_data = dhan.intraday_minute_data(
        security_id="2885", 
        exchange_segment="NSE_EQ", 
        instrument_type="EQUITY",
        from_date=today,
        to_date=today
    )
    
    print("Raw Response:", intraday_data)
    
except Exception as e:
    print(f"Error: {e}")
"""
    sftp = ssh.open_sftp()
    with sftp.file('/root/test_dhan.py', 'w') as f:
        f.write(test_script)
    sftp.close()
    
    stdin, stdout, stderr = ssh.exec_command("/root/backend/venv/bin/python /root/test_dhan.py")
    print(stdout.read().decode())
    
    ssh.close()
except Exception as e:
    print(f"Error: {e}")
