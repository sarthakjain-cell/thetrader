from strategy_base import BaseStrategy
import pandas as pd

class Strategy006VolumeClimax(BaseStrategy):
    def __init__(self):
        super().__init__("S006_VOLCLIMAX", "AI Volume Climax Absorption (Long-Only)")
        
    def evaluate(self, symbol: str, current_bar: pd.Series, context: dict) -> dict:
        signal_dict = {"signal": "HOLD", "reason": "", "stop_loss": None, "target": None, "conviction": 0.5}
        
        req_keys = ['Volume', 'Volume_SMA_20', 'ATR_14']
        for k in req_keys:
            if k not in current_bar or pd.isna(current_bar[k]):
                signal_dict["reason"] = f"Missing feature {k}"
                return signal_dict
                
        vol = current_bar['Volume']
        vol_avg = current_bar['Volume_SMA_20']
        atr = current_bar['ATR_14']
        
        open_p = current_bar['Open']
        close_p = current_bar['Close']
        low_p = current_bar['Low']
        high_p = current_bar['High']
        
        # 1. Volume Climax Filter (Volume > 3x Average)
        if vol_avg > 0 and vol > (vol_avg * 3):
            # 2. Reversal / Absorption Pattern
            # Large volume but the close is near the high of the bar, leaving a long lower wick (Panic selling absorbed)
            candle_range = high_p - low_p
            if candle_range > 0:
                close_from_low = close_p - low_p
                # If price closed in the top 40% of the candle despite massive volume
                if (close_from_low / candle_range) > 0.6:
                    
                    stop_loss = low_p - (atr * 0.5) # Hard stop below the climax low
                    target = close_p + (atr * 2.0)
                    
                    signal_dict["signal"] = "BUY"
                    signal_dict["reason"] = f"Volume Climax Absorption (Vol: {vol/vol_avg:.1f}x)"
                    signal_dict["stop_loss"] = stop_loss
                    signal_dict["target"] = target
                    signal_dict["conviction"] = 0.8 # High conviction on climax
                    return signal_dict
                    
        signal_dict["reason"] = "No volume climax setup"
        return signal_dict

    def manage_position(self, symbol: str, position: dict, current_bar: pd.Series) -> dict:
        low = current_bar['Low']
        high = current_bar['High']
        open_price = current_bar['Open']
        
        if low <= position['stop_loss']:
            return {"action": "CLOSE", "reason": "Climax Low Broken (Stop Hit)", "exit_price": min(open_price, position['stop_loss'])}
        elif high >= position['target']:
            return {"action": "CLOSE", "reason": "Target Hit", "exit_price": max(open_price, position['target'])}
            
        return {"action": "HOLD"}
