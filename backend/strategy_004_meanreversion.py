from strategy_base import BaseStrategy
import pandas as pd

class Strategy004MeanReversion(BaseStrategy):
    def __init__(self):
        super().__init__("S004_MEANREV", "AI Panic Fade (Long-Only)")
        
    def evaluate(self, symbol: str, current_bar: pd.Series, context: dict) -> dict:
        signal_dict = {"signal": "HOLD", "reason": "", "stop_loss": None, "target": None, "conviction": 0.5}
        
        req_keys = ['RSI_14', 'VWAP', 'ATR_14']
        for k in req_keys:
            if k not in current_bar or pd.isna(current_bar[k]):
                signal_dict["reason"] = f"Missing feature {k}"
                return signal_dict
                
        rsi = current_bar['RSI_14']
        vwap = current_bar['VWAP']
        atr = current_bar['ATR_14']
        
        close_p = current_bar['Close']
        open_p = current_bar['Open']
        
        # 1. Extreme Filter (Panic)
        # RSI < 25 (oversold) and price is extended far below VWAP
        distance_from_vwap = vwap - close_p
        
        if rsi < 25 and distance_from_vwap > (1.5 * atr):
            # 2. Reversal Trigger
            # Bullish candle (close > open) indicating panic might be pausing
            if close_p > open_p:
                stop_loss = current_bar['Low'] - (atr * 0.2) # Tight stop below the panic wick
                target = vwap # Mean reversion target is the mean itself
                
                
                # Check Sentiment Veto
                sentiment = context.get('sentiment', {}).get(symbol, 0)
                macro_neg = context.get('active_negative_stocks', set())
                
                if sentiment < -0.3:
                    signal_dict["reason"] = f"VETO: Negative Sentiment ({sentiment:.2f}) overrode panic fade"
                    return signal_dict
                if symbol in macro_neg:
                    signal_dict["reason"] = "VETO: Macro Headwind Active"
                    return signal_dict
                
                # Make sure reward/risk is logical
                risk = close_p - stop_loss
                reward = target - close_p
                if risk > 0 and (reward / risk) >= 1.0:
                    signal_dict["signal"] = "BUY"
                    signal_dict["reason"] = f"Panic extreme fade (RSI: {rsi:.1f}, Dist: {distance_from_vwap:.2f})"
                    signal_dict["stop_loss"] = stop_loss
                    signal_dict["target"] = target
                    signal_dict["conviction"] = 0.65
                    return signal_dict
                
        signal_dict["reason"] = "No extreme panic setup"
        return signal_dict

    def manage_position(self, symbol: str, position: dict, current_bar: pd.Series) -> dict:
        low = current_bar['Low']
        high = current_bar['High']
        open_price = current_bar['Open']
        
        if low <= position['stop_loss']:
            return {"action": "CLOSE", "reason": "Stop Loss Hit", "exit_price": min(open_price, position['stop_loss'])}
        elif high >= position['target']:
            return {"action": "CLOSE", "reason": "Target Hit (VWAP Reached)", "exit_price": max(open_price, position['target'])}
            
        return {"action": "HOLD"}
