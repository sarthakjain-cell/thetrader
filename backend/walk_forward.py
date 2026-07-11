import pandas as pd
import numpy as np
import sqlite3
import itertools
import ta
from logger import log

DB_PATH = "trading_system.db"

def load_data(table_name="historical_data_5y"):
    conn = sqlite3.connect(DB_PATH)
    # yfinance_fetcher saved it with 'Datetime' column
    df = pd.read_sql(f"SELECT * FROM {table_name} ORDER BY Datetime ASC", conn)
    conn.close()
    df['Datetime'] = pd.to_datetime(df['Datetime'])
    return df

def apply_strategy(df, fast_ema, slow_ema, rsi_thresh):
    """Applies the technical rules and returns a signal column."""
    temp_df = df.copy()
    temp_df['EMA_Fast'] = ta.trend.ema_indicator(temp_df['Close'], window=fast_ema)
    temp_df['EMA_Slow'] = ta.trend.ema_indicator(temp_df['Close'], window=slow_ema)
    temp_df['RSI'] = ta.momentum.rsi(temp_df['Close'], window=14)
    
    temp_df['Signal'] = 0
    # Buy Condition
    buy_cond = (temp_df['EMA_Fast'] > temp_df['EMA_Slow']) & (temp_df['RSI'] > rsi_thresh)
    # Sell Condition (Momentum loss)
    sell_cond = (temp_df['EMA_Fast'] < temp_df['EMA_Slow']) | (temp_df['RSI'] < 40)
    
    temp_df.loc[buy_cond, 'Signal'] = 1
    temp_df.loc[sell_cond, 'Signal'] = -1
    return temp_df

def run_backtest_window(df, slippage=0.0005, brokerage_rate=0.0005):
    """Simulates trading over a specific window of data."""
    position = 0
    capital = 100000.0
    initial_capital = capital
    buy_price = 0
    
    winning_trades = 0
    losing_trades = 0
    gross_profit = 0
    gross_loss = 0
    
    for i in range(1, len(df)):
        signal = df['Signal'].iloc[i]
        price = df['Close'].iloc[i]
        
        if signal == 1 and position == 0:
            # Buy
            exec_price = price * (1 + slippage)
            position = int(capital / exec_price)
            trade_value = position * exec_price
            fees = min(trade_value * brokerage_rate, 20.0)
            capital -= (trade_value + fees)
            buy_price = exec_price
            
        elif signal == -1 and position > 0:
            # Sell
            exec_price = price * (1 - slippage)
            trade_value = position * exec_price
            # Brokerage + STT (0.025%)
            fees = min(trade_value * brokerage_rate, 20.0) + (trade_value * 0.00025)
            capital += (trade_value - fees)
            
            pnl = trade_value - fees - (position * buy_price)
            if pnl > 0:
                winning_trades += 1
                gross_profit += pnl
            else:
                losing_trades += 1
                gross_loss += abs(pnl)
                
            position = 0
            buy_price = 0
            
    # Force close at end of window
    if position > 0:
        price = df['Close'].iloc[-1]
        exec_price = price * (1 - slippage)
        trade_value = position * exec_price
        fees = min(trade_value * brokerage_rate, 20.0) + (trade_value * 0.00025)
        capital += (trade_value - fees)
        pnl = trade_value - fees - (position * buy_price)
        if pnl > 0:
            winning_trades += 1
            gross_profit += pnl
        else:
            losing_trades += 1
            gross_loss += abs(pnl)
            
    net_profit = capital - initial_capital
    profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else 0
    win_rate = (winning_trades / (winning_trades + losing_trades)) if (winning_trades + losing_trades) > 0 else 0
    
    return {
        "net_profit": net_profit,
        "profit_factor": profit_factor,
        "win_rate": win_rate,
        "total_trades": winning_trades + losing_trades
    }

def walk_forward_optimization():
    log.info("Starting Walk-Forward Optimization Engine...")
    
    try:
        df = load_data()
    except Exception as e:
        log.error(f"Failed to load data: {e}")
        return
        
    if df.empty:
        log.error("No historical data found. Run yfinance_fetcher.py first.")
        return
        
    # Split data into 3 roughly equal time windows for Walk-Forward testing
    window_size = len(df) // 3
    w1 = df.iloc[0 : window_size]
    w2 = df.iloc[window_size : window_size*2]
    w3 = df.iloc[window_size*2 : ]
    
    # Train on W1, Test on W2. Then Train on W2, Test on W3.
    windows = [(w1, w2, "Window 1 (Train Y1-1.6, Test Y1.6-3.3)"), 
               (w2, w3, "Window 2 (Train Y1.6-3.3, Test Y3.3-5)")]
    
    # Define Parameter Grid
    fast_emas = [5, 9, 12, 15]
    slow_emas = [21, 26, 40, 50]
    rsi_thresholds = [50, 55, 60]
    
    combinations = list(itertools.product(fast_emas, slow_emas, rsi_thresholds))
    
    best_overall_params = None
    best_overall_pf = 0
    
    log.info(f"Testing {len(combinations)} parameter combinations across unseen Walk-Forward windows...")
    
    for fast_ema, slow_ema, rsi_thresh in combinations:
        if fast_ema >= slow_ema:
            continue # Skip invalid combinations
            
        valid_across_windows = True
        avg_test_pf = 0
        
        for train_df, test_df, window_name in windows:
            # 1. Train (Find if it works in-sample)
            train_signals = apply_strategy(train_df, fast_ema, slow_ema, rsi_thresh)
            train_results = run_backtest_window(train_signals)
            
            # If it fails in training, discard immediately to save time (we want Profit Factor > 1.2 at least)
            if train_results["profit_factor"] < 1.1 or train_results["total_trades"] < 5:
                valid_across_windows = False
                break
                
            # 2. Test (Does it survive unseen out-of-sample data?)
            test_signals = apply_strategy(test_df, fast_ema, slow_ema, rsi_thresh)
            test_results = run_backtest_window(test_signals)
            
            if test_results["profit_factor"] < 1.0: # Lost money on test data
                valid_across_windows = False
                break
                
            avg_test_pf += test_results["profit_factor"]
            
        if valid_across_windows:
            avg_test_pf /= len(windows)
            if avg_test_pf > best_overall_pf:
                best_overall_pf = avg_test_pf
                best_overall_params = (fast_ema, slow_ema, rsi_thresh)
                
    if best_overall_params:
        log.info(f"OPTIMIZATION COMPLETE! Found Mathematical Edge.")
        log.info(f"Winning Parameters: Fast EMA {best_overall_params[0]}, Slow EMA {best_overall_params[1]}, RSI > {best_overall_params[2]}")
        log.info(f"Average Out-of-Sample Profit Factor: {best_overall_pf:.2f}")
    else:
        log.warning("OPTIMIZATION FAILED. No parameter combination survived the unseen out-of-sample tests.")
        log.warning("Conclusion: A basic EMA+RSI strategy is mathematically broken on this asset. We must add new filters (e.g. ADX, Volume).")

if __name__ == "__main__":
    walk_forward_optimization()
