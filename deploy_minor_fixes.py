import paramiko
from scp import SCPClient

IP = "206.189.129.232"
USER = "root"
PASS = "MyroomNo.is133g"

print(f"Connecting to {IP}...")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(IP, username=USER, password=PASS, timeout=10)

with SCPClient(ssh.get_transport()) as scp:
    print("Uploading backend/data_provider.py...")
    scp.put('backend/data_provider.py', remote_path='/root/backend/data_provider.py')
    print("Uploading backend/live_trader.py...")
    scp.put('backend/live_trader.py', remote_path='/root/backend/live_trader.py')
    print("Uploading Strategies...")
    scp.put('backend/strategy_003_momentum.py', remote_path='/root/backend/strategy_003_momentum.py')
    scp.put('backend/strategy_004_meanreversion.py', remote_path='/root/backend/strategy_004_meanreversion.py')
    scp.put('backend/strategy_006_volclimax.py', remote_path='/root/backend/strategy_006_volclimax.py')

print("Restarting engine-a-technical via PM2...")
stdin, stdout, stderr = ssh.exec_command("pm2 restart engine-a-technical", get_pty=True)
stdout.read() # wait

ssh.close()
print("Done!")
