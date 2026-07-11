import pandas as pd
import numpy as np
import ta

class Backtester:
    def __init__(self, df, initial_capital=100000.0):
        self.df = df.copy()
        self.capital = initial_capital
        self.initial_capital = initial_capital
        self.position = 0
        self.buy_price = 0
        self.trades = []
        
    def calculate_fees(self, trade_value, is_sell=False):
        # Brokerage: 0.05% or ₹20, whichever is lower
        brokerage = min(trade_value * 0.0005, 20.0)
        # STT: 0.025% only on sell for intraday equity
        stt = (trade_value * 0.00025) if is_sell else 0.0
        # Exchange txn charge (~0.00325%), SEBI charges, GST, etc. (Simplifying to 0.005%)
        other_charges = trade_value * 0.00005
        return brokerage + stt + other_charges

    def simulate(self):
        # Slippage: 0.05%
        slippage_rate = 0.0005
        
        for i in range(len(self.df)):
            current_price = self.df['Close'].iloc[i]
            signal = self.df['Signal'].iloc[i]
            timestamp = self.df['Datetime'].iloc[i]
            
            # Entry logic (Long only for simplicity first)
            if signal == 1 and self.position == 0:
                # Add slippage to buy price (buying at a higher price)
                execution_price = current_price * (1 + slippage_rate)
                
                # Calculate max position size
                self.position = int(self.capital / execution_price)
                if self.position > 0:
                    trade_value = self.position * execution_price
                    fees = self.calculate_fees(trade_value, is_sell=False)
                    
                    self.capital -= (trade_value + fees)
                    self.buy_price = execution_price
                    
                    self.trades.append({
                        "type": "BUY",
                        "time": timestamp,
                        "price": execution_price,
                        "qty": self.position,
                        "fees": fees
                    })
                    
            # Exit logic
            elif signal == -1 and self.position > 0:
                # Subtract slippage from sell price (selling at a lower price)
                execution_price = current_price * (1 - slippage_rate)
                trade_value = self.position * execution_price
                fees = self.calculate_fees(trade_value, is_sell=True)
                
                self.capital += (trade_value - fees)
                
                # Record trade
                pnl = trade_value - fees - (self.position * self.buy_price)
                
                self.trades.append({
                    "type": "SELL",
                    "time": timestamp,
                    "price": execution_price,
                    "qty": self.position,
                    "fees": fees,
                    "pnl": pnl
                })
                
                self.position = 0
                self.buy_price = 0
                
        # Force square-off at the end of data
        if self.position > 0:
            current_price = self.df['Close'].iloc[-1]
            execution_price = current_price * (1 - slippage_rate)
            trade_value = self.position * execution_price
            fees = self.calculate_fees(trade_value, is_sell=True)
            self.capital += (trade_value - fees)
            
            pnl = trade_value - fees - (self.position * self.buy_price)
            self.trades.append({
                "type": "SELL (AUTO)",
                "time": self.df['Datetime'].iloc[-1],
                "price": execution_price,
                "qty": self.position,
                "fees": fees,
                "pnl": pnl
            })
            self.position = 0

    def print_results(self):
        net_profit = self.capital - self.initial_capital
        sell_trades = [t for t in self.trades if "SELL" in t["type"]]
        winning_trades = [t for t in sell_trades if t["pnl"] > 0]
        
        total_fees = sum(t["fees"] for t in self.trades)
        
        print("\n--- ENTERPRISE BACKTEST RESULTS ---")
        print(f"Initial Capital: Rs. {self.initial_capital:,.2f}")
        print(f"Final Capital:   Rs. {self.capital:,.2f}")
        print(f"Net Profit:      Rs. {net_profit:,.2f} ({(net_profit/self.initial_capital)*100:.2f}%)")
        print(f"Total Fees Paid: Rs. {total_fees:,.2f}")
        
        if len(sell_trades) > 0:
            win_rate = len(winning_trades) / len(sell_trades) * 100
            print(f"Total Completed Trades: {len(sell_trades)}")
            print(f"Win Rate:               {win_rate:.2f}%")
            
            gross_profits = sum(t["pnl"] for t in winning_trades)
            gross_losses = abs(sum(t["pnl"] for t in sell_trades if t["pnl"] <= 0))
            profit_factor = (gross_profits / gross_losses) if gross_losses > 0 else float('inf')
            print(f"Profit Factor:          {profit_factor:.2f}")

def apply_momentum_strategy(df):
    """
    Momentum Strategy: 
    - Fast EMA (9) crosses above Slow EMA (21)
    - RSI (14) > 55 (indicating strong upward momentum)
    """
    # Calculate indicators using 'ta' library
    df['EMA_9'] = ta.trend.ema_indicator(df['Close'], window=9)
    df['EMA_21'] = ta.trend.ema_indicator(df['Close'], window=21)
    df['RSI_14'] = ta.momentum.rsi(df['Close'], window=14)
    
    # Generate signals
    df['Signal'] = 0
    
    # Buy when momentum is strong
    buy_condition = (df['EMA_9'] > df['EMA_21']) & (df['RSI_14'] > 55)
    # Exit when EMA crosses back or RSI drops below 40
    sell_condition = (df['EMA_9'] < df['EMA_21']) | (df['RSI_14'] < 40)
    
    df.loc[buy_condition, 'Signal'] = 1
    df.loc[sell_condition, 'Signal'] = -1
    
    return df

if __name__ == "__main__":
    import sqlite3
    db_path = "trading_system.db"
    print(f"Loading 5-year baseline data from {db_path}...")
    try:
        conn = sqlite3.connect(db_path)
        df = pd.read_sql("SELECT * FROM historical_data_5y ORDER BY Datetime ASC", conn)
        conn.close()
        df['Datetime'] = pd.to_datetime(df['Datetime'])
        print("Applying Default Momentum Strategy (EMA 9/21 + RSI 55)...")
        df = apply_momentum_strategy(df)
        
        bt = Backtester(df)
        bt.simulate()
        bt.print_results()
    except Exception as e:
        print(f"Failed to run backtest: {e}")
