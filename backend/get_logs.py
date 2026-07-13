import subprocess

cmd = [
    "ssh",
    "-o", "ConnectTimeout=5",
    "root@206.189.129.232",
    "cat /root/.pm2/logs/training-monitor-error.log | tail -n 50"
]

print("Executing SSH command...")
try:
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
    print("--- STDOUT ---")
    print(result.stdout)
    print("--- STDERR ---")
    print(result.stderr)
    print(f"Exit code: {result.returncode}")
    
    with open("streamlit_error.log", "w") as f:
        f.write(result.stdout)
except Exception as e:
    print(f"Failed: {e}")
