import paramiko
import os

remote_host = '206.189.129.232'
remote_user = 'root'
remote_base_dir = '/root/backend'

files_to_upload = [
    'live_trader.py',
    'discord_alert.py',
    'daily_reporter.py',
    'training_monitor.py'
]

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

def clean_output(output):
    return output.replace('\n\n', '\n').strip()

try:
    print(f"Connecting to {remote_host}...")
    ssh.connect(remote_host, username=remote_user, password="MyroomNo.is133g")
    sftp = ssh.open_sftp()
    
    for file_name in files_to_upload:
        local_path = os.path.join(os.getcwd(), file_name)
        remote_path = f"{remote_base_dir}/{file_name}"
        if os.path.exists(local_path):
            print(f"Uploading {file_name}...")
            sftp.put(local_path, remote_path)
        else:
            print(f"Warning: {local_path} not found.")
            
    sftp.close()
    
    print("Installing 'requests' library on VPS...")
    stdin, stdout, stderr = ssh.exec_command(f'cd {remote_base_dir} && ./venv/bin/pip install requests')
    print(clean_output(stdout.read().decode('utf-8', errors='ignore')))
    
    print("Restarting 'live_trader'...")
    stdin, stdout, stderr = ssh.exec_command(f'cd {remote_base_dir} && pm2 restart live_trader')
    print(clean_output(stdout.read().decode('utf-8', errors='ignore')))
    
    print("Restarting 'training_monitor'...")
    stdin, stdout, stderr = ssh.exec_command(f'cd {remote_base_dir} && ./venv/bin/pip install streamlit plotly && pm2 delete training_monitor || true && pm2 start ./venv/bin/streamlit --name training_monitor -- run training_monitor.py --server.port 8501 --server.address 0.0.0.0')
    print(clean_output(stdout.read().decode('utf-8', errors='ignore')))
    
    print("Scheduling 'daily_reporter' cron (16:00 IST = 10:30 UTC)...")
    # PM2 servers usually run in UTC. 16:00 IST is 10:30 UTC. PM2 cron doesn't support 30m offsets easily in some syntaxes,
    # but "30 10 * * *" works (10:30 AM UTC = 4:00 PM IST)
    cron_cmd = f'cd {remote_base_dir} && pm2 delete daily_reporter || true && pm2 start ./venv/bin/python --name daily_reporter --cron "30 10 * * *" --no-autorestart -- daily_reporter.py && pm2 save'
    stdin, stdout, stderr = ssh.exec_command(cron_cmd)
    print(clean_output(stdout.read().decode('utf-8', errors='ignore')))
    
    print("Deployment of Epic 9 successful!")
    
except Exception as e:
    print(f"Deployment failed: {e}")
finally:
    ssh.close()
