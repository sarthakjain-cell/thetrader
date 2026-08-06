import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('206.189.129.232', username='root', password='MyroomNo.is133g')
stdin, stdout, stderr = ssh.exec_command('sqlite3 /root/backend/trading_system.db "SELECT * FROM paper_trades ORDER BY id DESC LIMIT 5;"')
print("OUT:", stdout.read().decode())
print("ERR:", stderr.read().decode())

stdin, stdout, stderr = ssh.exec_command('sqlite3 /root/backend/trading_system.db "SELECT * FROM paper_positions ORDER BY id DESC LIMIT 5;"')
print("OUT POS:", stdout.read().decode())
print("ERR POS:", stderr.read().decode())
ssh.close()
