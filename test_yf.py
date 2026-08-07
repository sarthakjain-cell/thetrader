import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('206.189.129.232', username='root', password='MyroomNo.is133g')
script = """import pandas as pd
import yfinance as yf
df = yf.download('RELIANCE.NS', period='1d', interval='5m', progress=False)
if isinstance(df.columns, pd.MultiIndex):
    df.columns = df.columns.droplevel(1)
df.reset_index(inplace=True)
print(df.columns.tolist())
"""
stdin, stdout, stderr = ssh.exec_command(f'/root/backend/venv/bin/python -c "{script}"')
print("OUT:", stdout.read().decode())
print("ERR:", stderr.read().decode())
ssh.close()
