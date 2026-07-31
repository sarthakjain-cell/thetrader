import paramiko

IP = '206.189.129.232'
USER = 'root'
PASS = 'MyroomNo.is133g'

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(IP, username=USER, password=PASS, timeout=10)
    
    sftp = ssh.open_sftp()
    
    files = [
        "backend/strategy_base.py",
        "backend/strategy_001_orb.py",
        "backend/strategy_002_vwap.py",
        "backend/optimizer.py",
        "backend/live_trader.py"
    ]
    
    for f in files:
        remote_path = f"/root/{f}"
        sftp.put(f, remote_path)
        print(f"Uploaded {f}")
        
    sftp.close()
    
    # Run Optimizer
    print("\nRunning Optimizer on Server (taking 15 seconds)...")
    stdin, stdout, stderr = ssh.exec_command("cd /root/backend && /root/backend/venv/bin/python optimizer.py")
    out = stdout.read().decode()
    err = stderr.read().decode()
    
    if out: print("STDOUT:\n", out)
    if err: print("STDERR:\n", err)
    
    # Restart Engine A to load new code
    print("\nRestarting Engine A (live_trader)...")
    ssh.exec_command("pm2 restart engine-a-technical")
    
    ssh.close()
    print("Deployment complete!")
except Exception as e:
    print(f"Error: {e}")
