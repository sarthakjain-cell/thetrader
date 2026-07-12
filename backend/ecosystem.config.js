module.exports = {
  apps: [
    {
      name: "algotrade-api",
      script: "./venv/bin/python",
      args: "-m uvicorn api:app --host 0.0.0.0 --port 8000",
      interpreter: "none",
      autorestart: true,
      watch: false,
      max_memory_restart: '1G'
    },
    {
      name: "engine-a-technical",
      script: "./venv/bin/python",
      args: "paper_trader.py",
      interpreter: "none",
      autorestart: true,
      watch: false,
      max_memory_restart: '500M'
    },
    {
      name: "engine-b-sentiment",
      script: "./venv/bin/python",
      args: "engine_b_advisor.py",
      interpreter: "none",
      autorestart: true,
      watch: false,
      max_memory_restart: '1500M' // FinBERT needs memory
    },
    {
      name: "ai-brain-daemon",
      script: "./venv/bin/python",
      args: "ai_brain_daemon.py",
      interpreter: "none",
      autorestart: true,
      watch: false,
      max_memory_restart: '300M'
    },
    {
      name: "ultimate-scraper",
      script: "./venv/bin/python",
      args: "ultimate_scraper.py",
      interpreter: "none",
      cron_restart: "*/15 * * * *",
      autorestart: false,
      watch: false,
      max_memory_restart: '300M'
    }
  ]
};
