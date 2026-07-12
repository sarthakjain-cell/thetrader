from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from sse_starlette.sse import EventSourceResponse
import sqlite3
import pandas as pd
import asyncio
import json
import time
import yfinance as yf

app = FastAPI(title="Algotrade Intraday Dashboard")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = "trading_system.db"

def get_db():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def fetch_dashboard_state(last_ah_id=0):
    conn = get_db()
    
    # 0. Market Status
    now = pd.Timestamp.now('Asia/Kolkata')
    current_time = now.time()
    from datetime import time as dtime
    is_weekday = now.weekday() < 5
    if current_time >= dtime(9, 15) and current_time <= dtime(15, 30) and is_weekday:
        market_status = "OPEN"
    else:
        market_status = "CLOSED"
    
    # 1. Account
    acc_df = pd.read_sql("SELECT * FROM paper_account WHERE id=1", conn)
    if acc_df.empty:
        account = {"equity": 0, "peak_equity": 0, "is_halted": 0, "mdd": 0}
    else:
        acc = acc_df.iloc[0]
        mdd = (acc['peak_equity'] - acc['equity']) / acc['peak_equity'] if acc['peak_equity'] > 0 else 0
        account = {"equity": acc['equity'], "peak_equity": acc['peak_equity'], "is_halted": acc['is_halted'], "mdd": mdd}
        
    # 2. Positions
    pos_df = pd.read_sql("SELECT * FROM paper_positions", conn)
    positions = pos_df.to_dict(orient="records")
    
    # 3. Today's Trades
    today = pd.Timestamp.now('Asia/Kolkata').strftime('%Y-%m-%d')
    trades_df = pd.read_sql(f"SELECT * FROM paper_trades WHERE exit_time LIKE '{today}%'", conn)
    trades = trades_df.to_dict(orient="records")
    
    # 4. Daily Summary (for rolling metrics)
    summary_df = pd.read_sql("SELECT * FROM daily_summary ORDER BY date DESC LIMIT 10", conn)
    if not summary_df.empty:
        rolling_pnl = summary_df['daily_pnl'].sum()
        total_trades = summary_df['trades_count'].sum()
    else:
        rolling_pnl = 0
        total_trades = 0
        
    # 5. Engine B Research Tips
    # Note for future optimization: Send this payload only when client first connects after 16:00
    # or when tips are newly generated, to reduce redundant data overhead.
    tips_df = pd.read_sql(f"SELECT * FROM research_tips WHERE date = '{today}'", conn)
    research_tips = tips_df.to_dict(orient="records")
        
    # 6. Live Market Signals (Scanner Heatmap)
    signals_df = pd.read_sql("SELECT * FROM market_signals", conn)
    market_signals = signals_df.to_dict(orient="records")
    
    # Attach AI Forecast probabilities
    forecasts_df = pd.read_sql(f"SELECT symbol, probability FROM daily_ai_forecasts WHERE date='{today}'", conn)
    forecasts_dict = dict(zip(forecasts_df.symbol, forecasts_df.probability))
    
    for sig in market_signals:
        sig['ai_prob'] = forecasts_dict.get(sig['symbol'], None)
        
    alerts = []
    if account.get('is_halted', False):
        alerts.append({"id": "kill_switch", "type": "critical", "message": "SYSTEM HALTED: Max Drawdown Exceeded", "timestamp": int(pd.Timestamp.now().timestamp())})
        
    for tip in research_tips:
        if tip['confidence'] == 'High':
            alerts.append({"id": f"tip_{tip['symbol']}_{today}", "type": "info", "message": f"High conviction tip generated for {tip['symbol']}", "timestamp": int(pd.Timestamp.now().timestamp())})

    # 7. After Hours Data
    after_hours_research = []
    pre_market_intelligence = []
    new_last_ah_id = last_ah_id
    
    if market_status == "CLOSED":
        if last_ah_id == 0:
            # First fetch: get the last 15 logs
            ah_df = pd.read_sql("SELECT * FROM after_hours_research ORDER BY id DESC LIMIT 15", conn)
            ah_df = ah_df.iloc[::-1] # Reverse for chronological
        else:
            # Subsequent fetch: only get new logs
            ah_df = pd.read_sql(f"SELECT * FROM after_hours_research WHERE id > {last_ah_id} ORDER BY id ASC", conn)
            
        if not ah_df.empty:
            after_hours_research = ah_df.to_dict(orient="records")
            new_last_ah_id = int(ah_df.iloc[-1]['id'])
            
        pmi_df = pd.read_sql("SELECT * FROM pre_market_intelligence", conn)
        pre_market_intelligence = pmi_df.to_dict(orient="records")

    conn.close()
    
    return {
        "market_status": market_status,
        "account": account,
        "positions": positions,
        "trades": trades,
        "research_tips": research_tips,
        "market_signals": market_signals,
        "alerts": alerts,
        "after_hours_research": after_hours_research,
        "pre_market_intelligence": pre_market_intelligence,
        "daily_ai_forecasts": [{"symbol": k, "probability": v} for k, v in forecasts_dict.items()],
        "rolling_metrics": {
            "pnl": rolling_pnl,
            "trades": int(total_trades)
        }
    }, new_last_ah_id

# In-memory cache for indices to prevent rate limits
indices_cache = {
    "data": [],
    "last_updated": 0
}

@app.get("/api/indices")
async def get_indices():
    global indices_cache
    now = time.time()
    
    # Serve from cache if less than 60 seconds old
    if now - indices_cache["last_updated"] < 60 and indices_cache["data"]:
        return indices_cache["data"]
        
    symbols = {
        "^NSEI": "Nifty 50",
        "^BSESN": "Sensex",
        "^NSEBANK": "Bank Nifty",
        "^INDIAVIX": "India VIX"
    }
    
    results = []
    
    # Run in thread to not block event loop
    def fetch_indices():
        data = []
        try:
            tickers = yf.Tickers(" ".join(symbols.keys()))
            for sym, name in symbols.items():
                df = tickers.tickers[sym].history(period="1d", interval="5m")
                if not df.empty:
                    current = df['Close'].iloc[-1]
                    # Get yesterday's close or first available today if market just opened
                    # Actually, yfinance gives 'Previous Close' via info, but info is slow.
                    # We can use the first 5m open of the day as a rough base, or fetch 2d.
                    # Fetching 5d ensures we have yesterday's close. Let's just fetch 5d 5m.
                    df_5d = tickers.tickers[sym].history(period="5d", interval="1d")
                    if len(df_5d) >= 2:
                        prev_close = df_5d['Close'].iloc[-2]
                    else:
                        prev_close = df['Open'].iloc[0]
                        
                    change = current - prev_close
                    pct_change = (change / prev_close) * 100
                    
                    # Sparkline: last 12 points (1 hour of 5m data)
                    sparkline = df['Close'].tail(12).tolist()
                    
                    data.append({
                        "name": name,
                        "value": round(current, 2),
                        "change": round(change, 2),
                        "pct_change": round(pct_change, 2),
                        "sparkline": sparkline
                    })
        except Exception as e:
            print(f"Error fetching indices: {e}")
        return data

    new_data = await asyncio.to_thread(fetch_indices)
    if new_data:
        indices_cache["data"] = new_data
        indices_cache["last_updated"] = now
        
    return indices_cache["data"]

@app.get("/api/news")
async def get_news(category: str = "All", limit: int = 20, offset: int = 0):
    conn = get_db()
    # If category != All, we filter by related_tickers. 
    # For now, related_tickers just has the raw ticker or MACRO_INDIA.
    # Future: we will build the full sector mapper in the Symbol Extractor job.
    if category.lower() != "all":
        query = f"SELECT * FROM scraped_news WHERE related_tickers LIKE '%{category}%' ORDER BY timestamp DESC LIMIT {limit} OFFSET {offset}"
    else:
        query = f"SELECT * FROM scraped_news ORDER BY timestamp DESC LIMIT {limit} OFFSET {offset}"
        
    try:
        df = pd.read_sql(query, conn)
        news = df.to_dict(orient="records")
    except Exception:
        news = []
    finally:
        conn.close()
        
    return news



@app.get("/api/bars/{symbol}")
async def get_bars(symbol: str):
    conn = get_db()
    # Fetch today's bars
    today = pd.Timestamp.now('Asia/Kolkata').strftime('%Y-%m-%d')
    df = pd.read_sql(f"SELECT * FROM intraday_5m WHERE symbol = '{symbol}' AND datetime LIKE '{today}%' ORDER BY datetime ASC", conn)
    conn.close()
    if df.empty:
        return []
    # Convert datetime to unix timestamp for lightweight-charts
    df['time'] = pd.to_datetime(df['datetime']).astype('int64') // 10**9
    df['value'] = df['volume']
    records = df[['time', 'open', 'high', 'low', 'close', 'value']].to_dict(orient='records')
    return records

@app.get("/api/equity_history")
async def get_equity_history():
    conn = get_db()
    df = pd.read_sql("SELECT date, daily_pnl FROM daily_summary ORDER BY date ASC", conn)
    conn.close()
    if df.empty:
        return []
    
    equity = 100000 # Base
    records = []
    for _, row in df.iterrows():
        equity += row['daily_pnl']
        records.append({
            "time": row['date'],
            "equity": equity,
            "peak": equity # fallback since we don't track historical peak
        })
    return records

@app.get("/api/poll")
async def poll_state():
    state, _ = await asyncio.to_thread(fetch_dashboard_state, 0)
    return state

@app.get("/api/stream")
async def stream_state():
    async def event_generator():
        last_ah_id = 0
        while True:
            # If client disconnects, asyncio.CancelledError is raised
            await asyncio.sleep(2) # Sleep for 2 seconds
            state, last_ah_id = await asyncio.to_thread(fetch_dashboard_state, last_ah_id)
            yield {
                    "event": "update",
                    "data": json.dumps(state)
                }
    return EventSourceResponse(event_generator(), headers={
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "*",
        "Access-Control-Allow-Methods": "*"
    })

from fastapi.staticfiles import StaticFiles
import os
# Mount the compiled Next.js frontend
if os.path.exists("frontend_out"):
    app.mount("/", StaticFiles(directory="frontend_out", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
