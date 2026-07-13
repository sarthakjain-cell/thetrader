import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="AI Training Monitor", layout="wide", page_icon="🤖")

DB_PATH = "trading_system.db"

def get_db():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def load_data():
    conn = get_db()
    
    # 1. Account
    try:
        acc_df = pd.read_sql("SELECT * FROM paper_account WHERE id=1", conn)
        acc = acc_df.iloc[0].to_dict() if not acc_df.empty else {"equity": 0, "peak_equity": 0}
    except:
        acc = {"equity": 0, "peak_equity": 0}
        
    # 2. Trades
    try:
        trades_df = pd.read_sql("SELECT * FROM paper_trades ORDER BY exit_time DESC", conn)
    except:
        trades_df = pd.DataFrame()
        
    # 3. Positions
    try:
        positions_df = pd.read_sql("SELECT * FROM paper_positions", conn)
    except:
        positions_df = pd.DataFrame()
        
    # 4. Generated Strategies
    try:
        gen_strat_df = pd.read_sql("SELECT * FROM generated_strategies ORDER BY profit_factor DESC", conn)
    except:
        gen_strat_df = pd.DataFrame()
        
    conn.close()
    return acc, trades_df, positions_df, gen_strat_df

st.title("🤖 AI Developer Training Monitor")
st.markdown("Raw diagnostic view of the AI's internal state and decision-making.")

acc, trades_df, positions_df, gen_strat_df = load_data()

# ----------------- TOP METRICS -----------------
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Paper Equity", f"₹{acc.get('equity', 0):,.2f}", 
              f"{acc.get('equity', 100000) - 100000:,.2f}")
    
with col2:
    peak = acc.get('peak_equity', 1)
    eq = acc.get('equity', 0)
    dd = ((peak - eq) / peak * 100) if peak > 0 else 0
    st.metric("Current Drawdown", f"{dd:.2f}%")
    
with col3:
    st.metric("Active Positions", len(positions_df))
    
with col4:
    total_pnl = trades_df['pnl'].sum() if not trades_df.empty else 0
    st.metric("Realized PnL (All Time)", f"₹{total_pnl:,.2f}")

st.divider()

# ----------------- STRATEGY LEADERBOARD -----------------
st.header("🏆 Live Strategy Leaderboard")
st.markdown("This shows how much money *each specific strategy* is making in live paper-trading.")

if not trades_df.empty:
    # Group trades by strategy
    strat_perf = trades_df.groupby('strategy_id').agg(
        Total_Trades=('id', 'count'),
        Total_PnL=('pnl', 'sum'),
        Win_Rate=('pnl', lambda x: (x > 0).mean() * 100)
    ).reset_index()
    
    strat_perf = strat_perf.sort_values(by="Total_PnL", ascending=False)
    
    # Format
    strat_perf['Total_PnL'] = strat_perf['Total_PnL'].apply(lambda x: f"₹{x:,.2f}")
    strat_perf['Win_Rate'] = strat_perf['Win_Rate'].apply(lambda x: f"{x:.1f}%")
    
    st.dataframe(strat_perf, use_container_width=True, hide_index=True)
else:
    st.info("No live trades executed yet.")
    
# ----------------- THE NIGHTLY FACTORY -----------------
st.header("🏭 Nightly Generated Strategies")
st.markdown("These are the most recent strategies invented and validated by the Nightly AI Factory.")

if not gen_strat_df.empty:
    display_df = gen_strat_df[['strategy_id', 'profit_factor', 'win_rate', 'total_trades', 'generation_date', 'config_json']]
    st.dataframe(display_df, use_container_width=True, hide_index=True)
else:
    st.info("No generated strategies in the database yet.")

st.divider()

# ----------------- RAW TRADE FEED -----------------
st.header("📜 Raw Trade Matrix")
st.markdown("A complete, unfiltered log of every decision the AI has made.")

if not trades_df.empty:
    # Color code PnL
    def color_pnl(val):
        color = 'green' if val > 0 else 'red'
        return f'color: {color}'
        
    styled_trades = trades_df[['exit_time', 'strategy_id', 'symbol', 'entry_price', 'exit_price', 'pnl', 'reason']]
    st.dataframe(styled_trades.style.map(color_pnl, subset=['pnl']), use_container_width=True, hide_index=True)
else:
    st.info("No trades to display.")
    
# ----------------- ACTIVE POSITIONS -----------------
st.header("🟢 Active Positions")
if not positions_df.empty:
    st.dataframe(positions_df, use_container_width=True, hide_index=True)
else:
    st.info("No active positions currently held by the AI.")

# ----------------- SYSTEM DIAGNOSTICS -----------------
st.divider()
st.header("🖥️ Server Health & Crash Logs")

colA, colB = st.columns(2)

with colA:
    st.subheader("PM2 Process Status")
    try:
        import subprocess
        result = subprocess.run(["pm2", "jlist"], capture_output=True, text=True)
        if result.returncode == 0:
            import json
            pm2_data = json.loads(result.stdout)
            pm2_df = pd.DataFrame([{
                "Process": p["name"],
                "Status": p["pm2_env"]["status"],
                "Restarts": p["pm2_env"]["restart_time"],
                "CPU": p["monit"]["cpu"] if p.get("monit") else 0,
                "RAM (MB)": round((p["monit"]["memory"] if p.get("monit") else 0) / 1024 / 1024, 1)
            } for p in pm2_data])
            
            # Color code status
            def color_status(val):
                color = 'green' if val == 'online' else 'red'
                return f'color: {color}'
                
            st.dataframe(pm2_df.style.map(color_status, subset=['Status']), use_container_width=True, hide_index=True)
        else:
            st.warning("Could not fetch PM2 status.")
    except Exception as e:
        st.error(f"PM2 Error: {e}")
        
with colB:
    st.subheader("Recent backend.log Errors")
    try:
        import os
        log_path = "backend.log"
        if os.path.exists(log_path):
            # Tail the last 100 lines and filter for ERROR or WARNING
            with open(log_path, 'r') as f:
                lines = f.readlines()
                
            recent_lines = lines[-500:]
            errors = [line.strip() for line in recent_lines if "ERROR" in line or "WARNING" in line]
            
            if errors:
                st.code("\n".join(errors[-10:]), language="text") # Show last 10 errors
            else:
                st.success("No recent errors found in backend.log")
        else:
            st.info("backend.log not found.")
    except Exception as e:
        st.error(f"Log Read Error: {e}")
