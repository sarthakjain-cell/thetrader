import sqlite3
import pandas as pd
from datetime import datetime
from discord_alert import send_discord_alert

DB_PATH = "trading_system.db"

def generate_eod_report():
    conn = sqlite3.connect(DB_PATH)
    today_str = datetime.now().strftime('%Y-%m-%d')
    
    # 1. Get today's trades
    try:
        trades_df = pd.read_sql(f"SELECT * FROM paper_trades WHERE exit_time LIKE '{today_str}%'", conn)
    except:
        trades_df = pd.DataFrame()
        
    # 2. Get active positions
    try:
        positions_df = pd.read_sql("SELECT * FROM paper_positions", conn)
    except:
        positions_df = pd.DataFrame()
        
    conn.close()
    
    total_trades = len(trades_df)
    
    if total_trades == 0 and positions_df.empty:
        message = "Market closed. No trades taken today and no active positions held."
        send_discord_alert(message, "📊 AI EOD Report (No Activity)", 0x808080)
        return
        
    if total_trades > 0:
        pnl_today = trades_df['pnl'].sum()
        wins = len(trades_df[trades_df['pnl'] > 0])
        losses = len(trades_df[trades_df['pnl'] <= 0])
        
        best_strat = trades_df.groupby('strategy_id')['pnl'].sum().idxmax() if not trades_df.empty else "N/A"
        
        color = 0x00ff00 if pnl_today >= 0 else 0xff0000
        
        message = f"**Daily Realized PnL:** ₹{pnl_today:,.2f}\n"
        message += f"**Total Trades:** {total_trades} ({wins} Wins, {losses} Losses)\n"
        message += f"**MVP Strategy:** {best_strat}\n\n"
    else:
        color = 0x0000ff
        message = "**Daily Realized PnL:** ₹0.00 (No closed trades)\n\n"
        
    if not positions_df.empty:
        message += f"**Active Positions ({len(positions_df)}):**\n"
        for _, row in positions_df.iterrows():
            message += f"- {row['symbol']} ({row['side']}) @ ₹{row['entry_price']}\n"
            
    send_discord_alert(message, f"📊 AI End-Of-Day Report ({today_str})", color)
    print("EOD Report sent to Discord.")

if __name__ == "__main__":
    generate_eod_report()
