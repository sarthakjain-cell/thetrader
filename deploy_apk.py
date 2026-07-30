import subprocess
import os

def run(cmd):
    print(f"Running: {cmd}")
    subprocess.run(cmd, shell=True, check=True)

try:
    os.chdir(r"c:\Users\sjain\OneDrive\Desktop\algotrade-ai\frontend")
    run("npm run build")
    run("npx cap sync")
    run("npx cap run android --target 1366634658002EO")
    print("Successfully pushed the update to the phone!")
except Exception as e:
    print(f"Deployment failed: {e}")
