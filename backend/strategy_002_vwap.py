from strategy_base import BaseStrategy
import pandas as pd
import ta

class Strategy002VWAP(BaseStrategy):
    def __init__(self):
        super().__init__("S002_VWAP", "VWAP Mean Reversion")
        
    def evaluate(self, symbol: str, current_bar: pd.Series, context: dict) -> dict:
        signal_dict = {"signal": "HOLD", "reason": "", "stop_loss": None, "target": None, "conviction": 0.5}
        
        if 'VWAP' not in current_bar or pd.isna(current_bar['VWAP']):
            signal_dict["reason"] = "VWAP not calculated"
            return signal_dict
            
        price = current_bar['Close']
        current_vwap = current_bar['VWAP']
        
        # Simple VWAP Bounce Logic
        # If price drops below VWAP by 0.5% and then closes above it? Or just mean reversion if it dips way below
        dist_from_vwap = (price - current_vwap) / current_vwap
        
        if dist_from_vwap < -0.01: # 1% below VWAP
            signal_dict["signal"] = "BUY"
            signal_dict["reason"] = f"Price ({price:.2f}) is >1% below VWAP ({current_vwap:.2f}). Reversion expected."
            signal_dict["stop_loss"] = price * 0.99 # 1% stop
            signal_dict["target"] = current_vwap # Target is VWAP
            signal_dict["conviction"] = 0.6
        else:
            signal_dict["reason"] = f"Price near VWAP. Dist: {dist_from_vwap*100:.2f}%"
            
        return signal_dict

    def manage_position(self, symbol: str, position: dict, current_bar: pd.Series) -> dict:
        low = current_bar['Low']
        high = current_bar['High']
        
        if low <= position['stop_loss']:
            return {"action": "CLOSE", "reason": "Stop Loss Hit", "exit_price": min(current_bar['Open'], position['stop_loss'])}
        elif high >= position['target']:
            return {"action": "CLOSE", "reason": "Target Hit", "exit_price": max(current_bar['Open'], position['target'])}
            
        return {"action": "HOLD"}
