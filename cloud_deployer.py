import os
import zipfile
import paramiko
from scp import SCPClient
import time
import sys
import subprocess

IP = "206.189.129.232"
USER = "root"
PASS = "MyroomNo.is133g"
LOCAL_DIR = "backend"
ZIP_NAME = "backend_clean.zip"

def create_zip():
    print("Zipping backend (excluding venv and pycache)...")
    with zipfile.ZipFile(ZIP_NAME, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(LOCAL_DIR):
            if 'venv' in dirs: dirs.remove('venv')
            if '__pycache__' in dirs: dirs.remove('__pycache__')
            for file in files:
                if file.endswith('.pyc') or file.endswith('.log') or file.endswith('.zip'):
                    continue
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, LOCAL_DIR)
                zipf.write(file_path, arcname)
                
        # Include frontend/out as frontend_out
        out_dir = os.path.join('frontend', 'out')
        if os.path.exists(out_dir):
            for root, dirs, files in os.walk(out_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.join('frontend_out', os.path.relpath(file_path, out_dir))
                    zipf.write(file_path, arcname)
    print("Zipping complete.")

def run_remote_command(ssh, command):
    print(f"\n--- Running: {command} ---")
    stdin, stdout, stderr = ssh.exec_command(command, get_pty=True)
    
    while True:
        line = stdout.readline()
        if not line:
            break
        try:
            print(line.strip().encode('ascii', 'ignore').decode('ascii'))
        except:
            pass
        sys.stdout.flush()
        
    exit_status = stdout.channel.recv_exit_status()
    if exit_status != 0:
        print(f"Error (Exit Code {exit_status})")
        err = stderr.read().decode()
        if err: print(err)
    return exit_status

def deploy():
    print("Building Next.js frontend for static export...")
    subprocess.run("npm run build", cwd="frontend", shell=True)
    
    create_zip()
    
    print(f"\nConnecting to {IP}...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(IP, username=USER, password=PASS, timeout=10)
    
    print("Uploading zip file...")
    with SCPClient(ssh.get_transport()) as scp:
        scp.put(ZIP_NAME, remote_path='~/backend.zip')
        
    print("\nExecuting server setup script...")
    
    setup_script = """
    export DEBIAN_FRONTEND=noninteractive
    echo 'Installing PM2 Process Manager...'
    npm install -g pm2
    
    echo 'Unpacking Code...'
    mkdir -p /root/backend
    unzip -o ~/backend.zip -d /root/backend
    cd /root/backend
    
    echo 'Building Python Virtual Environment...'
    python3 -m venv venv
    source venv/bin/activate
    
    echo 'Installing AI Libraries (This takes 2 minutes for FinBERT/PyTorch)...'
    pip install --upgrade pip
    pip install -r requirements.txt
    
    echo 'Starting the AI Engines...'
    pm2 delete all || true
    pm2 start ecosystem.config.js
    pm2 save
    pm2 startup systemd -u root --hp /root
    pm2 list
    """
    
    run_remote_command(ssh, setup_script)
    ssh.close()
    
    if os.path.exists(ZIP_NAME):
        os.remove(ZIP_NAME)
    print("\nDEPLOYMENT FULLY SUCCESSFUL!")

if __name__ == "__main__":
    deploy()
