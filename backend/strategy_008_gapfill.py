from strategy_base import BaseStrategy
import pandas as pd

class Strategy008GapFill(BaseStrategy):
    def __init__(self):
        super().__init__("S008_GAPFILL", "AI Gap Fill Reversion (Long-Only)")
        # Note: Since the engine is currently Long-Only for paper trading, 
        # we will trade 'Gap Downs' recovering back to yesterday's close.
        # A true gap fill strategy works both ways.
        
    def evaluate(self, symbol: str, current_bar: pd.Series, context: dict) -> dict:
        signal_dict = {"signal": "HOLD", "reason": "", "stop_loss": None, "target": None, "conviction": 0.5}
        
        req_keys = ['Prev_Close', 'ATR_14']
        for k in req_keys:
            if k not in current_bar or pd.isna(current_bar[k]):
                signal_dict["reason"] = f"Missing feature {k}"
                return signal_dict
                
        prev_close = current_bar['Prev_Close']
        atr = current_bar['ATR_14']
        
        open_p = current_bar['Open']
        close_p = current_bar['Close']
        
        # 1. Gap Filter (Did it gap down by more than 0.5%?)
        if prev_close > 0:
            gap_pct = (open_p - prev_close) / prev_close
            
            # Gap Down by at least 0.5%
            if gap_pct < -0.005:
                # 2. Trigger: Price starts pushing up strongly from the open
                # E.g. A strong green bar right after the gap down
                if close_p > open_p and (close_p - open_p) > (atr * 0.5):
                    
                    stop_loss = current_bar['Low'] - (atr * 0.2)
                    target = prev_close # Target is exactly the gap fill
                    
                    # Ensure risk-reward is somewhat sane
                    if target > close_p:
                        signal_dict["signal"] = "BUY"
                        signal_dict["reason"] = f"Gap Down Reversion (Gap: {gap_pct*100:.2f}%)"
                        signal_dict["stop_loss"] = stop_loss
                        signal_dict["target"] = target
                        signal_dict["conviction"] = 0.7
                        return signal_dict
                        
        signal_dict["reason"] = "No gap fill setup"
        return signal_dict

    def manage_position(self, symbol: str, position: dict, current_bar: pd.Series) -> dict:
        low = current_bar['Low']
        high = current_bar['High']
        open_price = current_bar['Open']
        
        if low <= position['stop_loss']:
            return {"action": "CLOSE", "reason": "Gap Fade Failed (Stop Hit)", "exit_price": min(open_price, position['stop_loss'])}
        elif high >= position['target']:
            return {"action": "CLOSE", "reason": "Gap Filled (Target Hit)", "exit_price": max(open_price, position['target'])}
            
        return {"action": "HOLD"}
