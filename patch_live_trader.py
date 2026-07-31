import paramiko

IP = '206.189.129.232'
USER = 'root'
PASS = 'MyroomNo.is133g'

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(IP, username=USER, password=PASS, timeout=10)
    
    print("Patching live_trader.py on the server...")
    
    sftp = ssh.open_sftp()
    remote_path = '/root/backend/live_trader.py'
    
    # Read the file
    file_obj = sftp.file(remote_path, 'r')
    content = file_obj.read().decode('utf-8')
    file_obj.close()
    
    # Modify SLEEP_INTERVAL_SECONDS to 300 (5 minutes)
    import re
    content = re.sub(r'SLEEP_INTERVAL_SECONDS = \d+', 'SLEEP_INTERVAL_SECONDS = 300', content)
    
    # Modify SYMBOLS list to only include 15 stocks to avoid rate limits
    symbols_replacement = '''SYMBOLS = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS", "SBIN.NS",
    "BHARTIARTL.NS", "ITC.NS", "HINDUNILVR.NS", "LT.NS", "BAJFINANCE.NS",
    "AXISBANK.NS", "KOTAKBANK.NS", "ASIANPAINT.NS", "MARUTI.NS"
]'''
    
    # Find the SYMBOLS list and replace it
    # We will use regex to find the SYMBOLS array block
    content = re.sub(r'SYMBOLS = \[[^\]]+\]', symbols_replacement, content, flags=re.DOTALL)
    
    # Write the modified content back
    file_obj = sftp.file(remote_path, 'w')
    file_obj.write(content.encode('utf-8'))
    file_obj.close()
    
    sftp.close()
    
    print("Restarting PM2...")
    stdin, stdout, stderr = ssh.exec_command("pm2 restart engine-a-technical")
    print(stdout.read().decode().strip())
    
    print("Successfully applied the anti-ban patch!")
    ssh.close()
except Exception as e:
    print(f"Error: {e}")
