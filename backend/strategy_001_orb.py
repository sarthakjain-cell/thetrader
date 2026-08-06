from strategy_base import BaseStrategy
import pandas as pd

class Strategy001ORB(BaseStrategy):
    def __init__(self):
        super().__init__("S001_ORB", "AI Open Range Breakout")
        
    def get_default_parameters(self) -> dict:
        return {
            'stop_loss_atr_mult': 1.5,
            'target_atr_mult': 3.0,
            'min_ml_prob': 0.55
        }
        
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
            # 1. Volume Confirmation
            vol = current_bar.get('Volume', 0)
            vol_sma = current_bar.get('Volume_SMA_20', 0)
            if vol <= vol_sma:
                signal_dict["reason"] = f"Breakout lacks volume confirmation (Vol: {vol} <= SMA: {vol_sma:.0f})"
                return signal_dict
                
            # 2. Momentum Confirmation
            rsi = current_bar.get('RSI_14', 50)
            if rsi < 55:
                signal_dict["reason"] = f"Breakout lacks momentum (RSI: {rsi:.1f} < 55)"
                return signal_dict
                
            atr = current_bar.get('ATR_14', price * 0.005)
                
            stop_loss = price - (atr * self.params['stop_loss_atr_mult'])
            target = price + (atr * self.params['target_atr_mult'])
            
            # Check Sentiment Veto
            sentiment = context.get('sentiment', {}).get(symbol, 0)
            macro_neg = context.get('active_negative_stocks', set())
            
            if sentiment < -0.3:
                signal_dict["reason"] = f"VETO: Negative Sentiment ({sentiment:.2f})"
                return signal_dict
            if symbol in macro_neg:
                signal_dict["reason"] = "VETO: Macro Headwind Active"
                return signal_dict
                
            # Check ML Oracle Probability
            ml_prob = context.get('ai_forecasts', {}).get(symbol, 0.5)
            
            min_prob = self.params['min_ml_prob']
            if ml_prob < min_prob:
                signal_dict["reason"] = f"VETO: AI predicts ORB failure ({ml_prob:.2f} < {min_prob})"
                return signal_dict
                
            signal_dict["signal"] = "BUY"
            signal_dict["reason"] = f"AI Vetted Breakout ({ml_prob:.2f} probability)"
            signal_dict["stop_loss"] = stop_loss
            signal_dict["target"] = target
            signal_dict["conviction"] = ml_prob
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

