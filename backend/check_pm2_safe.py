import paramiko

remote_host = '206.189.129.232'
remote_user = 'root'
password = 'MyroomNo.is133g'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    ssh.connect(remote_host, username=remote_user, password=password)
    
    # Run pm2 list with no-color to avoid ansi escape sequences
    stdin, stdout, stderr = ssh.exec_command('pm2 jlist')
    out = stdout.read().decode('utf-8', errors='ignore')
    
    # Parse json to avoid charmap print crash
    import json
    data = json.loads(out)
    for app in data:
        print(f"App: {app['name']}")
        print(f"  Status: {app['pm2_env']['status']}")
        if 'cron_restart' in app['pm2_env']:
             print(f"  Cron: {app['pm2_env']['cron_restart']}")
             
except Exception as e:
    print(f"Error: {e}")
finally:
    ssh.close()
