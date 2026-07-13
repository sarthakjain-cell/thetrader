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
      args: "live_trader.py",
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
    },
    {
      name: "daily-reporter",
      script: "./venv/bin/python",
      args: "daily_reporter.py",
      interpreter: "none",
      cron_restart: "0 11 * * 1-5", // 4:30 PM IST Mon-Fri
      autorestart: false,
      watch: false
    },
    {
      name: "nightly-factory",
      script: "./venv/bin/python",
      args: "nightly_factory.py",
      interpreter: "none",
      cron_restart: "30 11 * * 1-5", // 5:00 PM IST Mon-Fri
      autorestart: false,
      watch: false
    }
  ]
};
