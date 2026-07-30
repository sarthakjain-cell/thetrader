import subprocess
import os

def run_cmd(cmd):
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
    print(result.stdout)
    return result

os.chdir(r"c:\Users\sjain\OneDrive\Desktop\algotrade-ai")

run_cmd("git add .")
run_cmd('git commit -m "UI Overhaul, API crash fixes, Splash screen hydration fix, and Markdown rendering"')
run_cmd("git push origin main")

print("Successfully pushed to GitHub!")
