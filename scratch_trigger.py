import paramiko
import sys

IP = "206.189.129.232"
USER = "root"
PASS = "MyroomNo.is133g"

def trigger():
    print(f"Connecting to {IP}...")
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(IP, username=USER, password=PASS, timeout=10)
        
        print("Triggering night_researcher.py on the server...")
        # Run it in the background using nohup
        stdin, stdout, stderr = ssh.exec_command("cd /root/backend && nohup /root/backend/venv/bin/python night_researcher.py > /root/night.log 2>&1 &")
        
        print("Triggered successfully. It should take a minute to populate.")
        ssh.close()
    except Exception as e:
        print(f"Failed to connect: {e}")

if __name__ == "__main__":
    trigger()
