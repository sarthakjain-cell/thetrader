import random
import json
import sqlite3
import pandas as pd
from datetime import datetime
from walk_forward import load_data, run_strategy_backtest
from dynamic_strategy import DynamicStrategy
from logger import log

DB_PATH = "trading_system.db"
NUM_GENERATIONS = 50 # Start with 50 for speed

def generate_random_config(strategy_id):
    # Possible indicators to compare against fixed thresholds
    # We'll build simple 2-condition strategies
    
    rsi_threshold = random.choice([20, 25, 30, 35, 40])
    rsi_op = random.choice(["<", ">"])
    
    adx_threshold = random.choice([20, 25, 30, 35])
    adx_op = random.choice([">", "<"])
    
    sl_atr = round(random.uniform(0.5, 2.5), 1)
    tp_atr = round(random.uniform(1.0, 5.0), 1)
    
    config = {
        "id": strategy_id,
        "conditions": [
            {"indicator": "RSI_14", "operator": rsi_op, "value": rsi_threshold},
            {"indicator": "ADX_14", "operator": adx_op, "value": adx_threshold},
            {"indicator": "Close", "operator": ">", "value": "VWAP"} # Always require price > VWAP for long
        ],
        "stop_loss_atr": sl_atr,
        "take_profit_atr": tp_atr
    }
    return config

def run_factory():
    print(f"Starting Nightly Strategy Factory. Generating {NUM_GENERATIONS} strategies...")
    
    df = load_data()
    if df.empty:
        print("No historical data found. Aborting.")
        return
        
    last_date = df['Datetime'].max()
    df_30d = df[df['Datetime'] >= last_date - pd.Timedelta(days=30)]
    print(f"Using {len(df_30d)} bars (30 days) for validation.")
    
    valid_strategies = []
    
    for i in range(NUM_GENERATIONS):
        strat_id = f"GEN_{datetime.now().strftime('%m%d')}_{i:03d}"
        config = generate_random_config(strat_id)
        
        strategy = DynamicStrategy(json.dumps(config))
        
        # Suppress logging during massive backtest loops
        res = run_strategy_backtest(df_30d, strategy)
        
        pf = res["profit_factor"]
        trades = res["total_trades"]
        
        if pf > 1.5 and trades >= 3: # Lowered trade threshold to 3 for 30-day window
            valid_strategies.append({
                "strategy_id": strat_id,
                "pf": pf,
                "win_rate": res["win_rate"],
                "trades": trades,
                "config_json": json.dumps(config)
            })
            print(f"[PASS] {strat_id} | PF: {pf:.2f} | Trades: {trades}")
            
    # Sort and save top 3
    if not valid_strategies:
        print("No strategies passed the validation gates tonight.")
        return
        
    valid_strategies.sort(key=lambda x: x["pf"], reverse=True)
    top_3 = valid_strategies[:3]
    
    print("\n=== TOP 3 STRATEGIES ===")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    generation_date = datetime.now().strftime('%Y-%m-%d')
    
    # Delete old generated strategies
    cursor.execute("DELETE FROM generated_strategies")
    
    for s in top_3:
        print(f"{s['strategy_id']} | PF: {s['pf']:.2f} | WinRate: {s['win_rate']:.2f}")
        cursor.execute("""
            INSERT INTO generated_strategies 
            (strategy_id, generation_date, profit_factor, win_rate, total_trades, config_json)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (s['strategy_id'], generation_date, s['pf'], s['win_rate'], s['trades'], s['config_json']))
        
    conn.commit()
    conn.close()
    print("Top strategies saved to database. Ready for morning live execution.")

if __name__ == "__main__":
    import logging
    # Disable walk_forward logging to prevent terminal spam
    logging.getLogger("walk_forward").setLevel(logging.WARNING) 
    run_factory()
