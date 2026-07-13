from strategy_base import BaseStrategy
import pandas as pd

class Strategy005RangeFade(BaseStrategy):
    def __init__(self):
        super().__init__("S005_RANGE", "AI Support Fade (Long-Only)")
        self.daily_lows = {} # Stores previous day's low or early session low
        
    def evaluate(self, symbol: str, current_bar: pd.Series, context: dict) -> dict:
        signal_dict = {"signal": "HOLD", "reason": "", "stop_loss": None, "target": None, "conviction": 0.5}
        
        req_keys = ['ADX_14', 'ATR_14', 'ORB_Low', 'ORB_High']
        for k in req_keys:
            if k not in current_bar or pd.isna(current_bar[k]):
                signal_dict["reason"] = f"Missing feature {k}"
                return signal_dict
                
        adx = current_bar['ADX_14']
        atr = current_bar['ATR_14']
        support_level = current_bar['ORB_Low']
        resistance_level = current_bar['ORB_High']
        
        close_p = current_bar['Close']
        low_p = current_bar['Low']
        
        # 1. Chop Filter
        # ADX < 30 means no trend, highly likely to bounce between support and resistance
        if adx < 30:
            # 2. Support Test Trigger
            # Price dipped into support level zone
            support_zone_upper = support_level + (atr * 0.6)
            support_zone_lower = support_level - (atr * 0.6)
            
            if support_zone_lower <= low_p <= support_zone_upper:
                # Bullish rejection
                if close_p > current_bar['Open']:
                    stop_loss = support_zone_lower - (atr * 0.5)
                    target = resistance_level # Target the other side of the range
                    
                    signal_dict["signal"] = "BUY"
                    signal_dict["reason"] = f"Support bounce in chop (ADX: {adx:.1f})"
                    signal_dict["stop_loss"] = stop_loss
                    signal_dict["target"] = target
                    signal_dict["conviction"] = 0.6
                    return signal_dict
                    
        signal_dict["reason"] = "No range support setup"
        return signal_dict

    def manage_position(self, symbol: str, position: dict, current_bar: pd.Series) -> dict:
        low = current_bar['Low']
        high = current_bar['High']
        open_price = current_bar['Open']
        
        if low <= position['stop_loss']:
            return {"action": "CLOSE", "reason": "Support Broken (Stop Hit)", "exit_price": min(open_price, position['stop_loss'])}
        elif high >= position['target']:
            return {"action": "CLOSE", "reason": "Resistance Reached (Target Hit)", "exit_price": max(open_price, position['target'])}
            
        return {"action": "HOLD"}
