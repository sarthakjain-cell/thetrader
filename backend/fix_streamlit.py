import subprocess

cmd = [
    "ssh",
    "root@206.189.129.232",
    "cd /root/backend && pm2 delete training_monitor || true && pm2 start ./venv/bin/streamlit --name training_monitor -- run training_monitor.py --server.port 8501 --server.address 0.0.0.0 && pm2 save"
]

print("Executing SSH command...")
result = subprocess.run(cmd, capture_output=True, text=True)

print("--- STDOUT ---")
print(result.stdout)
print("--- STDERR ---")
print(result.stderr)
print(f"Exit code: {result.returncode}")
