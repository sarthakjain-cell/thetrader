import pandas as pd
import numpy as np
import ta

class StrategyV7VWAP:
    def __init__(self, df, params):
        self.df = df.copy()
        self.p = params
        
        atr_ind = ta.volatility.AverageTrueRange(self.df['High'], self.df['Low'], self.df['Close'], window=14)
        self.df['ATR'] = atr_ind.average_true_range()
        self.df['RSI'] = ta.momentum.rsi(self.df['Close'], window=14)
        
    def backtest(self, initial_capital=100000.0, risk_per_trade=0.01):
        capital = initial_capital
        position = 0
        buy_price = 0
        stop_loss = 0
        
        trades = []
        equity_curve = []
        
        slippage = 0.0005
        brokerage = 0.0005
        
        grouped = self.df.groupby(self.df['Datetime'].dt.date)
        
        for date, group in grouped:
            if group.empty: continue
            
            if position > 0:
                print(f"Warning: Position carried over from previous day on {date}")
                position = 0
                
            # Compute Daily VWAP
            group = group.copy()
            group['Cum_Vol'] = group['Volume'].cumsum()
            group['Cum_Vol_Price'] = (group['Volume'] * (group['High'] + group['Low'] + group['Close']) / 3).cumsum()
            group['VWAP'] = group['Cum_Vol_Price'] / group['Cum_Vol']
            
            entered_today = False
            
            for i in range(len(group)):
                row = group.iloc[i]
                price = row['Close']
                low = row['Low']
                high = row['High']
                vwap = row['VWAP']
                
                # EOD Liquidation at 15:25
                if row['Datetime'].hour == 15 and row['Datetime'].minute >= 25:
                    if position > 0:
                        exec_price = price * (1 - slippage)
                        trade_value = position * exec_price
                        fees = min(trade_value * brokerage, 20.0) + (trade_value * 0.00025)
                        capital += (trade_value - fees)
                        
                        pnl = trade_value - fees - (position * buy_price)
                        trades.append({"pnl": pnl, "type": "eod_stop"})
                        
                        position = 0
                        buy_price = 0
                    
                    equity_curve.append(capital)
                    continue
                
                if position > 0:
                    if low <= stop_loss:
                        exec_price = min(row['Open'], stop_loss) * (1 - slippage)
                        trade_value = position * exec_price
                        fees = min(trade_value * brokerage, 20.0) + (trade_value * 0.00025)
                        capital += (trade_value - fees)
                        
                        pnl = trade_value - fees - (position * buy_price)
                        trades.append({"pnl": pnl, "type": "stop"})
                        
                        position = 0
                        buy_price = 0
                        
                    elif high >= vwap:
                        exec_price = max(row['Open'], vwap) * (1 - slippage)
                        trade_value = position * exec_price
                        fees = min(trade_value * brokerage, 20.0) + (trade_value * 0.00025)
                        capital += (trade_value - fees)
                        
                        pnl = trade_value - fees - (position * buy_price)
                        trades.append({"pnl": pnl, "type": "target"})
                        
                        position = 0
                        buy_price = 0
                        
                if position == 0 and not entered_today and i > 5:
                    # Allow 5 bars (25 mins) for VWAP to stabilize
                    atr = row['ATR']
                    if (vwap - price) > (self.p['vwap_dev_atr'] * atr):
                        if row['RSI'] < self.p['vwap_rsi']:
                            exec_price = price * (1 + slippage)
                            
                            initial_stop_dist = atr * self.p['vwap_stop']
                            if initial_stop_dist > 0:
                                risk_amount = capital * risk_per_trade
                                qty = int(risk_amount / initial_stop_dist)
                                max_qty = int(capital / exec_price)
                                qty = min(qty, max_qty)
                                
                                if qty > 0:
                                    position = qty
                                    trade_value = position * exec_price
                                    fees = min(trade_value * brokerage, 20.0)
                                    capital -= (trade_value + fees)
                                    
                                    buy_price = exec_price
                                    stop_loss = buy_price - initial_stop_dist
                                    entered_today = True

                eq = capital + (position * price if position > 0 else 0)
                equity_curve.append(eq)

        winning_trades = [t for t in trades if t["pnl"] > 0]
        losing_trades = [t for t in trades if t["pnl"] <= 0]
        
        gross_profit = sum(t["pnl"] for t in winning_trades)
        gross_loss = abs(sum(t["pnl"] for t in losing_trades))
        pf = (gross_profit / gross_loss) if gross_loss > 0 else 0
        
        eq_series = pd.Series(equity_curve)
        if eq_series.empty:
            return {"pf": 0, "mdd": 1.0, "trades": 0, "net": 0, "equity": [initial_capital]}
            
        rolling_max = eq_series.cummax()
        drawdowns = (eq_series - rolling_max) / rolling_max
        mdd = abs(drawdowns.min()) if not drawdowns.empty else 0
        
        return {
            "pf": pf,
            "mdd": mdd,
            "trades": len(trades),
            "net": capital - initial_capital,
            "equity": equity_curve
        }
