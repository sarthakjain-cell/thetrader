from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from sse_starlette.sse import EventSourceResponse
import sqlite3
import pandas as pd
import asyncio
import json
import time
import os
import yfinance as yf
from pydantic import BaseModel
import google.generativeai as genai

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

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
        
    alerts = []
    
    # --- ENGINE HEALTH MONITOR (RED FLAGS) ---
    engine_stall = False
    try:
        # Check Engine A (Execution)
        sig_check = pd.read_sql("SELECT MAX(updated_at) as last_up FROM market_signals", conn)
        if not sig_check.empty and sig_check.iloc[0]['last_up']:
            last_sig_time = pd.to_datetime(sig_check.iloc[0]['last_up']).tz_localize('Asia/Kolkata')
            if market_status == "OPEN" and (now - last_sig_time).total_seconds() > 600:
                alerts.append({"id": "engine_a_stall", "type": "critical", "message": "🚨 ENGINE A (EXECUTION) STALLED! Data is stale.", "timestamp": int(now.timestamp())})
                engine_stall = True

        # Check Engine B (AI Advisor)
        news_check = pd.read_sql("SELECT MAX(timestamp) as last_news FROM scraped_news", conn)
        if not news_check.empty and news_check.iloc[0]['last_news']:
            last_news_time = pd.to_datetime(news_check.iloc[0]['last_news']).tz_localize('Asia/Kolkata')
            # If news is older than 2 hours (7200 seconds), flag it
            if (now - last_news_time).total_seconds() > 7200:
                alerts.append({"id": "engine_b_stall", "type": "critical", "message": "🚨 ENGINE B (AI) DISCONNECTED! Missing macro data.", "timestamp": int(now.timestamp())})
                engine_stall = True
    except Exception as e:
        print(f"Health monitor error: {e}")
        
    if engine_stall:
        # Force the market status to display STALLED in UI
        market_status = "STALLED"
        
    # 2. Positions
    pos_df = pd.read_sql("SELECT * FROM paper_positions", conn)
    if not pos_df.empty:
        if 'current_price' not in pos_df.columns:
            pos_df['current_price'] = pos_df['entry_price']
        if 'unrealized_pnl' not in pos_df.columns:
            pos_df['unrealized_pnl'] = 0.0
            
        # Optional: Try to join with market_signals to get real-time price
        try:
            sig_df = pd.read_sql("SELECT symbol, last_price FROM market_signals", conn)
            if not sig_df.empty:
                pos_df = pd.merge(pos_df, sig_df, on="symbol", how="left")
                pos_df['current_price'] = pos_df['last_price'].fillna(pos_df['current_price'])
                pos_df['unrealized_pnl'] = (pos_df['current_price'] - pos_df['entry_price']) * pos_df['qty']
                pos_df = pos_df.drop(columns=['last_price'])
        except:
            pass
            
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

    # Fetch Strategy Performance
    try:
        strat_df = pd.read_sql("SELECT strategy_id, profit_factor, win_rate, total_trades FROM generated_strategies ORDER BY profit_factor DESC", conn)
        
        # Calculate live PnL per strategy
        pnl_df = pd.read_sql("SELECT strategy_id, sum(pnl) as net_pnl FROM paper_trades GROUP BY strategy_id", conn)
        if not pnl_df.empty:
            strat_df = pd.merge(strat_df, pnl_df, on="strategy_id", how="left")
            strat_df['net_pnl'] = strat_df['net_pnl'].fillna(0.0)
        else:
            strat_df['net_pnl'] = 0.0
            
        strat_df['name'] = strat_df['strategy_id']
        strat_df['description'] = 'AI Managed Strategy'
        strat_df['is_active'] = 1
        strat_df['max_drawdown'] = 0.0
        
        strategies = strat_df.to_dict(orient="records")
    except Exception as e:
        print(f"Strategy fetch error: {e}")
        strategies = []

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
        },
        "strategies": strategies
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
        query = f"SELECT * FROM scraped_news WHERE related_tickers LIKE '%{category}%' AND source NOT IN ('SEBI', 'RBI') ORDER BY timestamp DESC LIMIT {limit} OFFSET {offset}"
    else:
        query = f"SELECT * FROM scraped_news WHERE source NOT IN ('SEBI', 'RBI') ORDER BY timestamp DESC LIMIT {limit} OFFSET {offset}"
        
    try:
        df = pd.read_sql(query, conn)
        
        # Ensure new Epic 15 columns exist even if old DB format
        if 'affected_sector' not in df.columns:
            df['affected_sector'] = "General Market"
        if 'action_signal' not in df.columns:
            df['action_signal'] = "⚪ HOLD"
        if 'confidence_score' not in df.columns:
            df['confidence_score'] = 0.5
            
        # Fix NaN values that cause JSON serialization crash
        import numpy as np
        df = df.replace({np.nan: None})
        
        # Replace None with default UI values for new rows that aren't enriched yet
        df['affected_sector'] = df['affected_sector'].fillna("General Market")
        df['action_signal'] = df['action_signal'].fillna("⚪ HOLD")
        
        news = df.to_dict(orient="records")
    except Exception as e:
        print(f"Error fetching news: {e}")
        news = []
    finally:
        conn.close()
        
    return news



@app.get("/api/bars/{symbol}")
async def get_bars(symbol: str):
    conn = get_db()
    # Fetch the most recent 150 bars for the symbol, regardless of date (fixes empty charts on weekends)
    df = pd.read_sql(f"SELECT * FROM intraday_5m WHERE symbol = '{symbol}' ORDER BY datetime DESC LIMIT 150", conn)
    conn.close()
    if df.empty:
        return []
        
    # Reverse to chronological order for the chart
    df = df.iloc[::-1].reset_index(drop=True)
    
    # Convert datetime to unix timestamp for lightweight-charts
    df['time'] = pd.to_datetime(df['datetime']).astype('int64') // 10**9
    df['value'] = df['volume']
    records = df[['time', 'open', 'high', 'low', 'close', 'value']].to_dict(orient='records')
    return records

@app.get("/api/insights/{symbol}")
async def get_insights(symbol: str):
    # Map symbols like 'RELIANCE' to 'RELIANCE.NS' if missing suffix
    yf_symbol = symbol if ".NS" in symbol else f"{symbol.split('.')[0]}.NS"
    
    def fetch_yf():
        try:
            t = yf.Ticker(yf_symbol)
            info = t.info
            
            fundamentals = {
                "todays_low": info.get("regularMarketDayLow", 0),
                "todays_high": info.get("regularMarketDayHigh", 0),
                "52_week_low": info.get("fiftyTwoWeekLow", 0),
                "52_week_high": info.get("fiftyTwoWeekHigh", 0),
                "open": info.get("regularMarketOpen", 0),
                "prev_close": info.get("regularMarketPreviousClose", 0),
                "volume": info.get("regularMarketVolume", 0),
                "mkt_cap": info.get("marketCap", 0),
                "pe_ratio": info.get("trailingPE", 0),
                "pb_ratio": info.get("priceToBook", 0),
                "roe": info.get("returnOnEquity", 0),
                "eps": info.get("trailingEps", 0),
                "div_yield": info.get("dividendYield", 0),
                "book_value": info.get("bookValue", 0),
                "debt_to_equity": info.get("debtToEquity", 0),
                "industry_pe": info.get("trailingPegRatio", 0), # Proxy
                "face_value": 1,
                "about": info.get("longBusinessSummary", "")
            }
            
            # Financials (Quarterly)
            financials = []
            try:
                inc = t.quarterly_income_stmt
                dates = inc.columns
                for d in dates[:5]:
                    financials.append({
                        "label": str(d)[:7], # YYYY-MM
                        "rev": float(inc.loc["Total Revenue", d]) if "Total Revenue" in inc.index else 0,
                        "prof": float(inc.loc["Net Income", d]) if "Net Income" in inc.index else 0
                    })
                financials.reverse() # Chronological
            except:
                pass
                
            # Shareholding
            shareholding = {
                "Promoters": 0,
                "Institutions": 0,
                "Retail": 0
            }
            try:
                holders = t.major_holders
                insiders = float(holders.loc[holders['Breakdown'] == 'insidersPercentHeld', 'Value'].values[0]) * 100
                inst = float(holders.loc[holders['Breakdown'] == 'institutionsPercentHeld', 'Value'].values[0]) * 100
                shareholding = {
                    "Promoters": round(insiders, 2),
                    "Institutions": round(inst, 2),
                    "Retail": round(100 - insiders - inst, 2)
                }
            except:
                pass
                
            return {
                "fundamentals": fundamentals,
                "financials": financials,
                "shareholding": shareholding
            }
        except Exception as e:
            print(f"Error fetching insights for {yf_symbol}: {e}")
            return None
            
    data = await asyncio.to_thread(fetch_yf)
    return data or {}

@app.post("/api/order")
async def place_order(request: Request):
    try:
        data = await request.json()
        symbol = data.get('symbol')
        action = data.get('action') # 'BUY' or 'SELL'
        price = data.get('price', 0.0)
        qty = data.get('qty', 10)
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Get account equity
        cursor.execute("SELECT equity FROM paper_account WHERE id=1")
        acc = cursor.fetchone()
        if not acc:
            conn.close()
            return JSONResponse({"status": "error", "message": "Account not found"})
        
        equity = acc[0]
        cost = price * qty
        
        if action == 'BUY':
            if equity < cost:
                conn.close()
                return JSONResponse({"status": "error", "message": "Insufficient funds"})
                
            cursor.execute("UPDATE paper_account SET equity = equity - ? WHERE id=1", (cost,))
            
            # Upsert position
            cursor.execute("SELECT qty, entry_price FROM paper_positions WHERE symbol=?", (symbol,))
            pos = cursor.fetchone()
            if pos:
                new_qty = pos[0] + qty
                new_entry = ((pos[1] * pos[0]) + cost) / new_qty
                cursor.execute("UPDATE paper_positions SET qty=?, entry_price=? WHERE symbol=?", (new_qty, new_entry, symbol))
            else:
                import datetime
                now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute("INSERT INTO paper_positions (symbol, qty, entry_price, strategy_id, entry_time, stop_loss, target) VALUES (?, ?, ?, ?, ?, ?, ?)", (symbol, qty, price, "MANUAL_OVERRIDE", now_str, 0.0, 0.0))
                
        elif action == 'SELL':
            cursor.execute("SELECT qty, entry_price FROM paper_positions WHERE symbol=?", (symbol,))
            pos = cursor.fetchone()
            if not pos or pos[0] < qty:
                conn.close()
                return JSONResponse({"status": "error", "message": "Insufficient quantity to sell"})
                
            cursor.execute("UPDATE paper_account SET equity = equity + ? WHERE id=1", (cost,))
            
            if pos[0] == qty:
                cursor.execute("DELETE FROM paper_positions WHERE symbol=?", (symbol,))
            else:
                cursor.execute("UPDATE paper_positions SET qty = qty - ? WHERE symbol=?", (qty, symbol))
                
            pnl = (price - pos[1]) * qty
            # Log trade
            import datetime
            now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("INSERT INTO paper_trades (symbol, strategy_id, direction, entry_time, exit_time, entry_price, exit_price, qty, pnl) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                           (symbol, "MANUAL", "LONG", now_str, now_str, pos[1], price, qty, pnl))
                           
        conn.commit()
        conn.close()
        
        return {"status": "success", "message": f"Manual {action} executed"}
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

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

class ChatRequest(BaseModel):
    message: str

@app.post("/api/chat")
async def chat_with_bot(request: ChatRequest):
    try:
        # Get live context
        state, _ = fetch_dashboard_state(0)
        portfolio_val = state.get("account", {}).get("equity", 0)
        
        system_prompt = f"""You are AlgoTrade AI, the intelligent institutional trading assistant for this platform.
Your goal is to help the user navigate the platform, understand their portfolio, and analyze the market.

PLATFORM UI MAP (Navigation):
- The main navigation bar is on the left side of the screen.
- To view "Holdings", tell the user to click the Briefcase icon on the left sidebar, OR you can navigate them automatically.
- To view "Intraday/Dashboard", tell them to click the Dashboard icon (the grid) on the left sidebar, OR navigate them.
- To start/stop the engine, they must go to the Dashboard and click the Deploy/Stop Engine button. You CANNOT do this for them.

CURRENT PORTFOLIO STATE:
- Current Equity: Rs {portfolio_val}

AGENTIC CAPABILITIES (The Security Sandbox):
If the user explicitly asks to switch pages or go to a specific view (like holdings, dashboard, or engine control), you MUST respond with ONLY a JSON object and nothing else. The frontend will execute this JSON.
Allowed JSON actions:
- {{"action": "NAVIGATE", "target": "holdings"}}
- {{"action": "NAVIGATE", "target": "dashboard"}}

For all other general chat, market analysis, or questions, reply in normal conversational Markdown. 
DO NOT output JSON unless you want to physically move the user's screen.
NEVER attempt to output a STOP_ENGINE or PLACE_TRADE action (they are blocked by the frontend anyway).
"""
        
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=system_prompt
        )
        
        response = model.generate_content(request.message)
        response_text = response.text.strip()
        
        # Check if the AI decided to use an Agentic JSON Action
        try:
            # If it starts with { and ends with }, parse it
            if response_text.startswith('{') and response_text.endswith('}'):
                action_data = json.loads(response_text)
                return {"type": "action", "data": action_data}
        except:
            pass
            
        return {"type": "text", "message": response_text}
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

from fastapi.staticfiles import StaticFiles
import os
# Mount the compiled Next.js frontend
if os.path.exists("frontend_out"):
    app.mount("/", StaticFiles(directory="frontend_out", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
