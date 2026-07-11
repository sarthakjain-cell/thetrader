import paramiko
import os

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("206.189.129.232", username="root", password="MyroomNo.is133g")
ssh.exec_command("rm -rf /root/backend/frontend_out/*")

sftp = ssh.open_sftp()
local_dir = r"c:\Users\sjain\OneDrive\Desktop\algotrade-ai\frontend\out"
remote_dir = "/root/backend/frontend_out"

def put_dir(l_dir, r_dir):
    try:
        sftp.mkdir(r_dir)
    except:
        pass
    for item in os.listdir(l_dir):
        l_item = os.path.join(l_dir, item)
        r_item = r_dir + "/" + item
        if os.path.isdir(l_item):
            put_dir(l_item, r_item)
        else:
            sftp.put(l_item, r_item)

put_dir(local_dir, remote_dir)
sftp.close()
ssh.close()
print("Frontend uploaded successfully.")
