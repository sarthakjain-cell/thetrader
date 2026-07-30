import paramiko

IP = '206.189.129.232'
USER = 'root'
PASS = 'MyroomNo.is133g'

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(IP, username=USER, password=PASS, timeout=10)
    
    # Check venv python
    stdin, stdout, stderr = ssh.exec_command("/root/backend/venv/bin/python -m pip install fastapi uvicorn pydantic google-generativeai python-dotenv sse-starlette")
    print("PIP INSTALL:", stdout.read().decode())
    print("PIP ERRORS:", stderr.read().decode())
    
    # Restart PM2
    ssh.exec_command("pm2 restart algotrade-api")
    
    # Wait a few seconds for crash
    import time
    time.sleep(2)
    
    # Check logs
    stdin, stdout, stderr = ssh.exec_command("cat /root/.pm2/logs/algotrade-api-error.log | tail -n 10")
    print("ERRORS:")
    print(stdout.read().decode())
    
    ssh.close()
except Exception as e:
    print(f"Error: {e}")
