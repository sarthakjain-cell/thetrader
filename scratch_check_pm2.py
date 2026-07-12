import paramiko
import sys

IP = "206.189.129.232"
USER = "root"
PASS = "MyroomNo.is133g"

def check_pm2():
    print(f"Connecting to {IP}...")
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(IP, username=USER, password=PASS, timeout=10)
        
        print("--- PM2 Engine Status ---")
        stdin, stdout, stderr = ssh.exec_command("pm2 list", get_pty=True)
        print(stdout.read().decode('ascii', 'ignore'))
        
        print("\n--- Recent Logs (Engine A) ---")
        stdin, stdout, stderr = ssh.exec_command("pm2 logs engine-a-technical --lines 10 --nostream", get_pty=True)
        print(stdout.read().decode('ascii', 'ignore'))
        
        print("\n--- Recent Logs (AI Brain Daemon) ---")
        stdin, stdout, stderr = ssh.exec_command("pm2 logs ai-brain-daemon --lines 10 --nostream", get_pty=True)
        print(stdout.read().decode('ascii', 'ignore'))
        
        ssh.close()
    except Exception as e:
        print(f"Failed to connect: {e}")

if __name__ == "__main__":
    check_pm2()
