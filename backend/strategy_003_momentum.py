from strategy_base import BaseStrategy
import pandas as pd

class Strategy003Momentum(BaseStrategy):
    def __init__(self):
        super().__init__("S003_MOMENTUM", "AI Trend Pullback (Long-Only)")
        
    def evaluate(self, symbol: str, current_bar: pd.Series, context: dict) -> dict:
        signal_dict = {"signal": "HOLD", "reason": "", "stop_loss": None, "target": None, "conviction": 0.5}
        
        # Need required features
        req_keys = ['ADX_14', 'VWAP', 'EMA_9', 'EMA_21', 'ATR_14']
        for k in req_keys:
            if k not in current_bar or pd.isna(current_bar[k]):
                signal_dict["reason"] = f"Missing feature {k}"
                return signal_dict
                
        adx = current_bar['ADX_14']
        vwap = current_bar['VWAP']
        ema9 = current_bar['EMA_9']
        ema21 = current_bar['EMA_21']
        atr = current_bar['ATR_14']
        
        open_p = current_bar['Open']
        close_p = current_bar['Close']
        low_p = current_bar['Low']
        
        # 1. Trend Filter
        if adx > 30 and close_p > vwap and ema9 > ema21:
            # 2. Trigger (Rejection off 9 EMA)
            # Price dipped below EMA9 during the bar but closed above it
            if low_p < ema9 and close_p > ema9:
                
                stop_loss = close_p - (atr * 1.5)
                # Momentum strategies don't have hard targets, they trail stops
                target = close_p + (atr * 5.0) # Arbitrary far target, mostly relies on trailing stop
                
                signal_dict["signal"] = "BUY"
                signal_dict["reason"] = f"Bullish rejection off 9 EMA (ADX: {adx:.1f})"
                signal_dict["stop_loss"] = stop_loss
                signal_dict["target"] = target
                signal_dict["conviction"] = 0.7
                return signal_dict
                
        signal_dict["reason"] = "No momentum pullback setup"
        return signal_dict

    def manage_position(self, symbol: str, position: dict, current_bar: pd.Series) -> dict:
        low = current_bar['Low']
        high = current_bar['High']
        close_p = current_bar['Close']
        open_price = current_bar['Open']
        
        # Hard Stops
        if low <= position['stop_loss']:
            return {"action": "CLOSE", "reason": "Stop Loss Hit", "exit_price": min(open_price, position['stop_loss'])}
        elif high >= position['target']:
            return {"action": "CLOSE", "reason": "Target Hit", "exit_price": max(open_price, position['target'])}
            
        # Trailing Stop: Trail slightly below the current close if it moves in our favor
        atr = current_bar.get('ATR_14', close_p * 0.005)
        potential_new_stop = close_p - (atr * 1.5)
        
        if potential_new_stop > position['stop_loss']:
            return {"action": "UPDATE_STOP", "new_stop": potential_new_stop, "reason": "Trailing stop up"}
            
        return {"action": "HOLD"}
