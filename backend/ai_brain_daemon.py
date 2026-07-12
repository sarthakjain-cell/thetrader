import time
import asyncio
from datetime import datetime
from zoneinfo import ZoneInfo
from logger import log
import subprocess
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def get_ist_now():
    return datetime.now(ZoneInfo('Asia/Kolkata'))

async def run_script(script_name):
    script_path = os.path.join(BASE_DIR, script_name)
    log.info(f"[Daemon] Launching {script_name}...")
    try:
        process = await asyncio.create_subprocess_exec(
            "python", script_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        if process.returncode == 0:
            log.info(f"[Daemon] {script_name} finished successfully.")
        else:
            log.error(f"[Daemon] {script_name} failed with code {process.returncode}")
            log.error(stderr.decode())
    except Exception as e:
        log.error(f"[Daemon] Error running {script_name}: {e}")

async def daemon_loop():
    log.info("[Daemon] 24/7 Macro-Economic AI Brain initialized.")
    
    # Flags to prevent running multiple times per day
    ran_harvester_today = False
    ran_economist_today = False
    ran_synthesizer_today = False
    
    while True:
        now = get_ist_now()
        
        # Reset daily flags at midnight
        if now.hour == 0 and now.minute < 5:
            ran_harvester_today = False
            ran_economist_today = False
            ran_synthesizer_today = False
        
        # 1. Market Hours (09:15 - 15:30) - Tactical Analyst
        # For daytime, we could launch a fast intraday trend checker. 
        # For now, it sleeps/idles to protect the CPU for Engine A.
        if now.hour >= 9 and (now.hour < 15 or (now.hour == 15 and now.minute <= 30)):
            log.info("[Daemon] Market is OPEN. Tactical Analyst mode engaged. Protecting CPU for Engine A.")
            await asyncio.sleep(600) # Sleep for 10 minutes
            
        # 2. Post-Market (15:31 - 23:59) - Ultimate Macro Scraper
        elif (now.hour > 15 or (now.hour == 15 and now.minute > 30)) and not ran_harvester_today:
            log.info("[Daemon] Market is CLOSED. Acting as Data Harvester. Scraping macro news (SEBI/RBI/Finance)...")
            await run_script("ultimate_scraper.py")
            # Also trigger the night researcher to calculate multi-timeframe trends
            log.info("[Daemon] Triggering Night Researcher for Technical Trend updates...")
            await run_script("night_researcher.py")
            ran_harvester_today = True
            
        # 3. Deep Night (00:00 - 04:00) - Pro Macro-Economist
        elif now.hour >= 0 and now.hour < 4 and not ran_economist_today:
            log.info("[Daemon] Deep Night. Acting as Pro Macro-Economist. Running NLP sentiment analysis...")
            await run_script("macro_engine.py")
            ran_economist_today = True
            
        # 4. Pre-Market (04:00 - 09:14) - Synthesizer
        elif now.hour >= 4 and now.hour < 9 and not ran_synthesizer_today:
            log.info("[Daemon] Pre-Market. Acting as Synthesizer. Injecting NLP features and training AI...")
            await run_script("model_trainer.py")
            ran_synthesizer_today = True
            
        else:
            log.info(f"[Daemon] Phase complete. Resting at {now.strftime('%H:%M:%S')}...")
            await asyncio.sleep(60) # check every minute

if __name__ == "__main__":
    asyncio.run(daemon_loop())
