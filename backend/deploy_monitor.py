import paramiko
import os

remote_host = '206.189.129.232'
remote_user = 'root'
remote_base_dir = '/root/backend'

files_to_upload = [
    'training_monitor.py'
]

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

def clean_output(output):
    return output.replace('\n\n', '\n').strip()

try:
    print(f"Connecting to {remote_host}...")
    ssh.connect(remote_host, username=remote_user)
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
    
    print("Installing 'streamlit' library on VPS...")
    stdin, stdout, stderr = ssh.exec_command(f'cd {remote_base_dir} && ./venv/bin/pip install streamlit plotly')
    print("Pip Install Output:")
    print(clean_output(stdout.read().decode('utf-8', errors='ignore')))
    
    print("Starting PM2 process 'training_monitor'...")
    # Stop it first if it exists
    ssh.exec_command(f'cd {remote_base_dir} && pm2 delete training_monitor')
    
    # Start streamlit via PM2
    start_cmd = f'cd {remote_base_dir} && pm2 start ./venv/bin/streamlit --name training_monitor -- run training_monitor.py --server.port 8501 && pm2 save'
    stdin, stdout, stderr = ssh.exec_command(start_cmd)
    print("PM2 Output:")
    print(clean_output(stdout.read().decode('utf-8', errors='ignore')))
    
    print("Deployment of Training Monitor successful!")
    
except Exception as e:
    print(f"Deployment failed: {e}")
finally:
    ssh.close()
