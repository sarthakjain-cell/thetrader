import pandas as pd
import numpy as np
import ta

class StrategyV6A:
    def __init__(self, df, params):
        self.df = df.copy()
        self.p = params
        
        # Core Indicators
        self.df['EMA_10'] = ta.trend.ema_indicator(self.df['Close'], window=10)
        self.df['RSI'] = ta.momentum.rsi(self.df['Close'], window=14)
        
        adx_ind = ta.trend.ADXIndicator(self.df['High'], self.df['Low'], self.df['Close'], window=14)
        self.df['ADX'] = adx_ind.adx()
        
        atr_ind = ta.volatility.AverageTrueRange(self.df['High'], self.df['Low'], self.df['Close'], window=14)
        self.df['ATR'] = atr_ind.average_true_range()
        
        # Donchian 20-Day
        self.df['Donchian_High_20'] = self.df['High'].rolling(window=20).max()
        self.df['Donchian_Low_20'] = self.df['Low'].rolling(window=20).min()
        
        # Drop warm-up
        self.df = self.df.dropna()
        
    def backtest(self, initial_capital=100000.0, risk_per_trade=0.01):
        capital = initial_capital
        position = 0
        buy_price = 0
        stop_loss = 0
        profit_target = 0
        
        trades = []
        equity_curve = [initial_capital]
        
        slippage = 0.0005
        brokerage = 0.0005
        
        for i in range(1, len(self.df)):
            row = self.df.iloc[i]
            price = row['Close']
            low = row['Low']
            high = row['High']
            
            if position > 0:
                # Check stops and targets
                # If both hit on same day, assume stop hit first (conservative)
                if low <= stop_loss:
                    exec_price = min(row['Open'], stop_loss) * (1 - slippage)
                    trade_value = position * exec_price
                    fees = min(trade_value * brokerage, 20.0) + (trade_value * 0.00025)
                    capital += (trade_value - fees)
                    
                    pnl = trade_value - fees - (position * buy_price)
                    trades.append({"pnl": pnl, "type": "stop"})
                    
                    position = 0
                    buy_price = 0
                    
                elif high >= profit_target:
                    exec_price = max(row['Open'], profit_target) * (1 - slippage)
                    trade_value = position * exec_price
                    fees = min(trade_value * brokerage, 20.0) + (trade_value * 0.00025)
                    capital += (trade_value - fees)
                    
                    pnl = trade_value - fees - (position * buy_price)
                    trades.append({"pnl": pnl, "type": "target"})
                    
                    position = 0
                    buy_price = 0
                    
            if position == 0:
                # Entry Condition Mode A
                donchian_dist = row['Donchian_High_20'] - row['Donchian_Low_20']
                donchian_10_pct = row['Donchian_Low_20'] + (0.10 * donchian_dist)
                
                if row.get('Entry_Allowed', False) and row.get('Market_Regime_Up', False):
                    if (row['Close'] < row['EMA_10']) and (row['Close'] <= donchian_10_pct):
                        if (row['RSI'] < self.p['rsi_thresh_a']) and (row['ADX'] > 20):
                            
                            exec_price = price * (1 + slippage)
                            atr = row['ATR']
                            
                            initial_stop_dist = atr * self.p['atr_stop_a']
                            if initial_stop_dist <= 0: continue
                            
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
                                profit_target = buy_price + (atr * self.p['atr_target_a'])

            eq = capital + (position * price if position > 0 else 0)
            equity_curve.append(eq)
            
        if position > 0:
            price = self.df.iloc[-1]['Close']
            exec_price = price * (1 - slippage)
            trade_value = position * exec_price
            fees = min(trade_value * brokerage, 20.0) + (trade_value * 0.00025)
            capital += (trade_value - fees)
            pnl = trade_value - fees - (position * buy_price)
            trades.append({"pnl": pnl, "type": "close"})
            equity_curve.append(capital)
            
        winning_trades = [t for t in trades if t["pnl"] > 0]
        losing_trades = [t for t in trades if t["pnl"] <= 0]
        
        gross_profit = sum(t["pnl"] for t in winning_trades)
        gross_loss = abs(sum(t["pnl"] for t in losing_trades))
        pf = (gross_profit / gross_loss) if gross_loss > 0 else 0
        
        eq_series = pd.Series(equity_curve)
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
