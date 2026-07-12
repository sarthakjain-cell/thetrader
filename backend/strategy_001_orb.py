from strategy_base import BaseStrategy
import pandas as pd
import ta

class Strategy001ORB(BaseStrategy):
    def __init__(self):
        super().__init__("S001_ORB", "AI Open Range Breakout")
        self.orb_bars = 6 # 30 min if 5 min bars
        self.orb_highs = {}
        
    def evaluate(self, symbol: str, df: pd.DataFrame, context: dict) -> dict:
        signal_dict = {"signal": "HOLD", "reason": "", "stop_loss": None, "target": None, "conviction": 0.5}
        
        if len(df) < self.orb_bars:
            signal_dict["reason"] = f"Waiting for ORB formation ({len(df)}/{self.orb_bars} bars)"
            return signal_dict
            
        if symbol not in self.orb_highs:
            self.orb_highs[symbol] = df.iloc[:self.orb_bars]['High'].max()
            
        latest_bar = df.iloc[-1]
        price = latest_bar['Close']
        
        if price > self.orb_highs[symbol]:
            # Calculate ATR for stops
            df_ta = df.copy()
            atr = 0.0
            if len(df_ta) >= 14:
                atr_ind = ta.volatility.AverageTrueRange(df_ta['High'], df_ta['Low'], df_ta['Close'], window=14)
                atr = atr_ind.average_true_range().iloc[-1]
            
            if atr == 0:
                atr = price * 0.005 # fallback 0.5%
                
            stop_loss = price - (atr * 1.0)
            target = price + (atr * 2.0)
            
            # Check context vetoes
            if symbol in context.get('active_negative_stocks', set()):
                signal_dict["signal"] = "VETO"
                signal_dict["reason"] = "MACRO VETO: Active global headwind."
                return signal_dict
                
            signal_dict["signal"] = "BUY"
            signal_dict["reason"] = f"ORB Breakout above {self.orb_highs[symbol]:.2f}"
            signal_dict["stop_loss"] = stop_loss
            signal_dict["target"] = target
            signal_dict["conviction"] = 0.8
        else:
            signal_dict["reason"] = f"Price {price:.2f} below ORB high {self.orb_highs[symbol]:.2f}"
            
        return signal_dict

    def manage_position(self, symbol: str, position: dict, df: pd.DataFrame) -> dict:
        latest_bar = df.iloc[-1]
        low = latest_bar['Low']
        high = latest_bar['High']
        
        if low <= position['stop_loss']:
            return {"action": "CLOSE", "reason": "Stop Loss Hit", "exit_price": min(latest_bar['Open'], position['stop_loss'])}
        elif high >= position['target']:
            return {"action": "CLOSE", "reason": "Target Hit", "exit_price": max(latest_bar['Open'], position['target'])}
            
        return {"action": "HOLD"}
