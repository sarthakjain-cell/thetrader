import pandas as pd
import numpy as np
import sqlite3
from logger import log
from feature_engine import compute_features
from strategy_001_orb import Strategy001ORB

DB_PATH = "trading_system.db"

def load_data(table_name="historical_data_5y"):
    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql(f"SELECT * FROM {table_name} ORDER BY Datetime ASC", conn)
    except Exception as e:
        log.error(f"Failed to load table {table_name}: {e}")
        return pd.DataFrame()
    finally:
        conn.close()
        
    df['Datetime'] = pd.to_datetime(df['Datetime'])
    return df

def run_strategy_backtest(df, strategy, slippage=0.0005, brokerage_rate=0.0005, initial_capital=100000.0):
    """
    Simulates trading over a dataset using a pluggable strategy.
    """
    if df.empty:
        return {"error": "Empty dataframe"}
        
    df = df.copy()
    
    # 1. Precompute features
    log.info(f"Computing features for {len(df)} bars...")
    df = compute_features(df)
    
    capital = initial_capital
    position_dict = None
    
    winning_trades = 0
    losing_trades = 0
    gross_profit = 0
    gross_loss = 0
    
    log.info(f"Starting backtest for {strategy.name} ({strategy.strategy_id})...")
    
    # Context can hold any global backtest state
    context = {}
    
    for i in range(1, len(df)):
        current_bar = df.iloc[i]
        symbol = "BACKTEST" # We assume single-symbol continuous series for now
        
        if position_dict is not None:
            # Manage Open Position
            res = strategy.manage_position(symbol, position_dict, current_bar)
            
            if res.get("action") == "UPDATE_STOP":
                position_dict["stop_loss"] = res["new_stop"]
                
            elif res.get("action") == "CLOSE":
                exec_price = res["exit_price"] if res.get("exit_price") is not None else current_bar['Close']
                trade_value = position_dict['qty'] * exec_price
                # Brokerage + STT (0.025%)
                fees = min(trade_value * brokerage_rate, 20.0) + (trade_value * 0.00025)
                capital += (trade_value - fees)
                
                pnl = trade_value - fees - (position_dict['qty'] * position_dict['entry_price'])
                if pnl > 0:
                    winning_trades += 1
                    gross_profit += pnl
                else:
                    losing_trades += 1
                    gross_loss += abs(pnl)
                    
                position_dict = None
                
        if position_dict is None:
            # Evaluate for new entries
            signal_dict = strategy.evaluate(symbol, current_bar, context)
            
            if signal_dict.get("signal") == "BUY":
                # Buy
                price = current_bar['Close']
                exec_price = price * (1 + slippage)
                qty = int((capital * 0.1) / exec_price) # Allocate 10% per trade max in backtest to simulate meta-allocator slice
                if qty > 0:
                    trade_value = qty * exec_price
                    fees = min(trade_value * brokerage_rate, 20.0)
                    capital -= (trade_value + fees)
                    
                    position_dict = {
                        "symbol": symbol,
                        "qty": qty,
                        "entry_price": exec_price,
                        "stop_loss": signal_dict.get("stop_loss"),
                        "target": signal_dict.get("target")
                    }
            
    # Force close at end of window
    if position_dict is not None:
        price = df.iloc[-1]['Close']
        exec_price = price * (1 - slippage)
        trade_value = position_dict['qty'] * exec_price
        fees = min(trade_value * brokerage_rate, 20.0) + (trade_value * 0.00025)
        capital += (trade_value - fees)
        pnl = trade_value - fees - (position_dict['qty'] * position_dict['entry_price'])
        if pnl > 0:
            winning_trades += 1
            gross_profit += pnl
        else:
            losing_trades += 1
            gross_loss += abs(pnl)
            
    net_profit = capital - initial_capital
    if gross_loss > 0:
        profit_factor = gross_profit / gross_loss
    elif gross_profit > 0:
        profit_factor = float('inf')
    else:
        profit_factor = 0
        
    win_rate = (winning_trades / (winning_trades + losing_trades)) if (winning_trades + losing_trades) > 0 else 0
    max_drawdown = 0 # Future: calculate MDD curve
    
    res = {
        "net_profit": net_profit,
        "profit_factor": profit_factor,
        "win_rate": win_rate,
        "total_trades": winning_trades + losing_trades,
        "max_drawdown": max_drawdown
    }
    
    log.info(f"Backtest Complete for {strategy.name}: PF={profit_factor:.2f}, Win Rate={win_rate*100:.1f}%, Trades={res['total_trades']}")
    return res

if __name__ == "__main__":
    df = load_data()
    if not df.empty:
        # Filter last 60 days
        last_date = df['Datetime'].max()
        df_60d = df[df['Datetime'] >= last_date - pd.Timedelta(days=60)]
        
        strategy = Strategy001ORB()
        results = run_strategy_backtest(df_60d, strategy)
        print("\n=== Final Backtest Results ===")
        print(results)
    else:
        print("No historical data found. Please run historical fetcher.")
