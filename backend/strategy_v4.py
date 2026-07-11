import pandas as pd
import numpy as np
import ta

class StrategyV4:
    def __init__(self, df, params):
        self.df = df.copy()
        self.p = params
        
        self.df['EMA_Fast'] = ta.trend.ema_indicator(self.df['Close'], window=self.p['fast_ema'])
        self.df['EMA_Slow'] = ta.trend.ema_indicator(self.df['Close'], window=self.p['slow_ema'])
        self.df['RSI'] = ta.momentum.rsi(self.df['Close'], window=14)
        
        adx_ind = ta.trend.ADXIndicator(self.df['High'], self.df['Low'], self.df['Close'], window=14)
        self.df['ADX'] = adx_ind.adx()
        
        atr_ind = ta.volatility.AverageTrueRange(self.df['High'], self.df['Low'], self.df['Close'], window=14)
        self.df['ATR'] = atr_ind.average_true_range()
        
        # Drop NaNs to prevent logic errors on warmup
        self.df = self.df.dropna()
        
    def backtest(self, initial_capital=100000.0, risk_per_trade=0.01):
        capital = initial_capital
        position = 0
        buy_price = 0
        stop_loss = 0
        
        trades = []
        equity_curve = [initial_capital]
        
        slippage = 0.0005
        brokerage = 0.0005
        
        for i in range(1, len(self.df)):
            row = self.df.iloc[i]
            price = row['Close']
            low = row['Low']
            
            if position > 0:
                if low <= stop_loss:
                    exec_price = min(row['Open'], stop_loss) * (1 - slippage)
                    trade_value = position * exec_price
                    fees = min(trade_value * brokerage, 20.0) + (trade_value * 0.00025)
                    capital += (trade_value - fees)
                    
                    pnl = trade_value - fees - (position * buy_price)
                    trades.append({"pnl": pnl})
                    
                    position = 0
                    buy_price = 0
                    
                elif row['EMA_Fast'] < row['EMA_Slow']:
                    exec_price = price * (1 - slippage)
                    trade_value = position * exec_price
                    fees = min(trade_value * brokerage, 20.0) + (trade_value * 0.00025)
                    capital += (trade_value - fees)
                    
                    pnl = trade_value - fees - (position * buy_price)
                    trades.append({"pnl": pnl})
                    
                    position = 0
                    buy_price = 0
                    
            if position == 0:
                # Engine Entry relies on Pre-computed `Entry_Allowed`
                if row.get('Entry_Allowed', False) and (row['EMA_Fast'] > row['EMA_Slow']) and (row['RSI'] > self.p['rsi_thresh']) and (row['ADX'] > self.p['adx_thresh']):
                    
                    exec_price = price * (1 + slippage)
                    atr = row['ATR']
                    
                    initial_stop_dist = atr * self.p['stop_atr_mult']
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

            eq = capital + (position * price if position > 0 else 0)
            equity_curve.append(eq)
            
        if position > 0:
            price = self.df.iloc[-1]['Close']
            exec_price = price * (1 - slippage)
            trade_value = position * exec_price
            fees = min(trade_value * brokerage, 20.0) + (trade_value * 0.00025)
            capital += (trade_value - fees)
            pnl = trade_value - fees - (position * buy_price)
            trades.append({"pnl": pnl})
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
