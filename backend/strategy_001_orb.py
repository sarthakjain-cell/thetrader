from strategy_base import BaseStrategy
import pandas as pd

class Strategy001ORB(BaseStrategy):
    def __init__(self):
        super().__init__("S001_ORB", "AI Open Range Breakout")
        
    def evaluate(self, symbol: str, current_bar: pd.Series, context: dict) -> dict:
        signal_dict = {"signal": "HOLD", "reason": "", "stop_loss": None, "target": None, "conviction": 0.5}
        
        # Check if ORB has formed (feature_engine returns NaN or something if not enough bars, 
        # but feature_engine sets it to max high if <6 bars. We assume it's valid if after 09:45)
        # Note: In backtesting, we just rely on ORB_High existing.
        
        if 'ORB_High' not in current_bar or pd.isna(current_bar['ORB_High']):
            signal_dict["reason"] = "Waiting for ORB formation"
            return signal_dict
            
        price = current_bar['Close']
        orb_high = current_bar['ORB_High']
        
        if price > orb_high:
            atr = current_bar.get('ATR_14', price * 0.005)
                
            stop_loss = price - (atr * 1.0)
            target = price + (atr * 2.0)
            
            # Check Sentiment Veto
            sentiment = context.get('sentiment', {}).get(symbol, 0)
            macro_neg = context.get('active_negative_stocks', set())
            
            if sentiment < -0.3:
                signal_dict["reason"] = f"VETO: Negative Sentiment ({sentiment:.2f})"
                return signal_dict
            if symbol in macro_neg:
                signal_dict["reason"] = "VETO: Macro Headwind Active"
                return signal_dict
                
            signal_dict["signal"] = "BUY"
            signal_dict["reason"] = f"ORB Breakout above {orb_high:.2f}"
            signal_dict["stop_loss"] = stop_loss
            signal_dict["target"] = target
            signal_dict["conviction"] = 0.8
        else:
            signal_dict["reason"] = f"Price {price:.2f} below ORB high {orb_high:.2f}"
            
        return signal_dict

    def manage_position(self, symbol: str, position: dict, current_bar: pd.Series) -> dict:
        low = current_bar['Low']
        high = current_bar['High']
        open_price = current_bar['Open']
        
        if low <= position['stop_loss']:
            return {"action": "CLOSE", "reason": "Stop Loss Hit", "exit_price": min(open_price, position['stop_loss'])}
        elif high >= position['target']:
            return {"action": "CLOSE", "reason": "Target Hit", "exit_price": max(open_price, position['target'])}
            
        return {"action": "HOLD"}

