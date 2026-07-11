import pandas as pd
import numpy as np
import sqlite3
import ta

DB_PATH = "trading_system.db"

def load_data():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM historical_data_5y ORDER BY Datetime ASC", conn)
    conn.close()
    df['Datetime'] = pd.to_datetime(df['Datetime'])
    return df

def apply_winning_strategy(df):
    fast_ema, slow_ema, rsi_thresh = 5, 21, 55
    df['EMA_Fast'] = ta.trend.ema_indicator(df['Close'], window=fast_ema)
    df['EMA_Slow'] = ta.trend.ema_indicator(df['Close'], window=slow_ema)
    df['RSI'] = ta.momentum.rsi(df['Close'], window=14)
    
    df['Signal'] = 0
    buy_cond = (df['EMA_Fast'] > df['EMA_Slow']) & (df['RSI'] > rsi_thresh)
    sell_cond = (df['EMA_Fast'] < df['EMA_Slow']) | (df['RSI'] < 40)
    
    df.loc[buy_cond, 'Signal'] = 1
    df.loc[sell_cond, 'Signal'] = -1
    return df

def calculate_metrics(df):
    slippage = 0.0005
    brokerage_rate = 0.0005
    
    position = 0
    capital = 100000.0
    initial_capital = capital
    buy_price = 0
    
    trades = []
    equity_curve = [initial_capital]
    
    for i in range(1, len(df)):
        signal = df['Signal'].iloc[i]
        price = df['Close'].iloc[i]
        
        # Entry
        if signal == 1 and position == 0:
            exec_price = price * (1 + slippage)
            position = int(capital / exec_price)
            trade_value = position * exec_price
            fees = min(trade_value * brokerage_rate, 20.0)
            capital -= (trade_value + fees)
            buy_price = exec_price
            
        # Exit
        elif signal == -1 and position > 0:
            exec_price = price * (1 - slippage)
            trade_value = position * exec_price
            # Brokerage + STT
            fees = min(trade_value * brokerage_rate, 20.0) + (trade_value * 0.00025)
            capital += (trade_value - fees)
            
            pnl = trade_value - fees - (position * buy_price)
            trades.append({"pnl": pnl})
            
            position = 0
            buy_price = 0
            
        # Mark to market for daily equity calculation
        current_equity = capital
        if position > 0:
            current_equity += position * price
        equity_curve.append(current_equity)
            
    # Close any open positions at the end
    if position > 0:
        price = df['Close'].iloc[-1]
        exec_price = price * (1 - slippage)
        trade_value = position * exec_price
        fees = min(trade_value * brokerage_rate, 20.0) + (trade_value * 0.00025)
        capital += (trade_value - fees)
        pnl = trade_value - fees - (position * buy_price)
        trades.append({"pnl": pnl})
        equity_curve.append(capital)
            
    # Calculate advanced metrics
    net_profit = capital - initial_capital
    
    winning_trades = [t for t in trades if t["pnl"] > 0]
    losing_trades = [t for t in trades if t["pnl"] <= 0]
    
    gross_profit = sum(t["pnl"] for t in winning_trades)
    gross_loss = abs(sum(t["pnl"] for t in losing_trades))
    
    profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else 0
    win_rate = (len(winning_trades) / len(trades)) if len(trades) > 0 else 0
    
    avg_win = np.mean([t["pnl"] for t in winning_trades]) if winning_trades else 0
    avg_loss = abs(np.mean([t["pnl"] for t in losing_trades])) if losing_trades else 0
    win_loss_ratio = (avg_win / avg_loss) if avg_loss > 0 else 0
    
    # Drawdown
    equity_series = pd.Series(equity_curve)
    rolling_max = equity_series.cummax()
    drawdown = (equity_series - rolling_max) / rolling_max
    max_drawdown = abs(drawdown.min())
    
    # Annualized Return & Sharpe (Assuming ~252 trading days/year for daily data)
    total_days = len(df)
    years = total_days / 252
    ann_return = ((capital / initial_capital) ** (1/years)) - 1 if years > 0 else 0
    
    daily_returns = equity_series.pct_change().dropna()
    ann_volatility = daily_returns.std() * np.sqrt(252)
    risk_free_rate = 0.07 # ~7% risk free rate in India
    sharpe_ratio = (ann_return - risk_free_rate) / ann_volatility if ann_volatility > 0 else 0
    
    print("\n=== COMPLETE VALIDATION REPORT (EMA 5/21 + RSI 55) ===")
    print(f"Total Trades:           {len(trades)}")
    print(f"Win Rate:               {win_rate*100:.2f}%")
    print(f"Profit Factor:          {profit_factor:.2f}")
    print(f"Average Win:            Rs. {avg_win:.2f}")
    print(f"Average Loss:           Rs. {avg_loss:.2f}")
    print(f"Avg Win/Loss Ratio:     {win_loss_ratio:.2f}")
    print("-----------------------------------------------------")
    print(f"Max Drawdown:           {max_drawdown*100:.2f}%")
    print(f"Annualized Return:      {ann_return*100:.2f}%")
    print(f"Annualized Volatility:  {ann_volatility*100:.2f}%")
    print(f"Sharpe Ratio:           {sharpe_ratio:.2f}")
    print("=====================================================\n")
    
    # Generate Jupyter Python Code Block for Equity Curve
    print("--- JUPYTER PLOT CODE ---")
    print("Run the following code in a Jupyter Notebook cell to plot the equity curve:")
    print("```python")
    print("import matplotlib.pyplot as plt")
    print(f"equity_data = {equity_curve[::10]} # Sampled every 10 days for brevity")
    print("plt.figure(figsize=(10,5))")
    print("plt.plot(equity_data, color='green')")
    print("plt.title('Backtest Equity Curve (EMA 5/21 + RSI 55)')")
    print("plt.xlabel('Time (Sampled)')")
    print("plt.ylabel('Capital (Rs.)')")
    print("plt.grid(True)")
    print("plt.show()")
    print("```")

if __name__ == "__main__":
    df = load_data()
    df = apply_winning_strategy(df)
    calculate_metrics(df)
