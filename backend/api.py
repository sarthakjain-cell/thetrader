from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from sse_starlette.sse import EventSourceResponse
import sqlite3
import pandas as pd
import asyncio
import json

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
        "rolling_metrics": {
            "pnl": rolling_pnl,
            "trades": int(total_trades)
        }
    }, new_last_ah_id



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
