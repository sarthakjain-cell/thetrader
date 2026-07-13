from strategy_base import BaseStrategy
import pandas as pd
import json

class DynamicStrategy(BaseStrategy):
    def __init__(self, config_json: str):
        self.config = json.loads(config_json)
        strat_id = self.config.get("id", "GEN_UNKNOWN")
        super().__init__(strat_id, f"AI Generated: {strat_id}")
        
    def evaluate(self, symbol: str, current_bar: pd.Series, context: dict) -> dict:
        signal_dict = {"signal": "HOLD", "reason": "", "stop_loss": None, "target": None, "conviction": 0.5}
        
        # Check Sentiment Veto
        sentiment = context.get('sentiment', {}).get(symbol, 0)
        macro_neg = context.get('active_negative_stocks', set())
        
        if sentiment < -0.3:
            signal_dict["reason"] = f"VETO: Negative Sentiment ({sentiment:.2f})"
            return signal_dict
        if symbol in macro_neg:
            signal_dict["reason"] = "VETO: Macro Headwind Active"
            return signal_dict

        # Evaluate conditions
        all_passed = True
        failed_reason = ""
        
        for cond in self.config.get("conditions", []):
            ind = cond["indicator"]
            op = cond["operator"]
            val = cond["value"]
            
            # If value is a string, assume it refers to another indicator (e.g. "Close" > "VWAP")
            if isinstance(val, str) and val in current_bar:
                compare_val = current_bar[val]
            else:
                compare_val = float(val)
                
            if ind not in current_bar or pd.isna(current_bar[ind]):
                all_passed = False
                failed_reason = f"Missing {ind}"
                break
                
            current_val = current_bar[ind]
            
            if op == "<":
                if not (current_val < compare_val):
                    all_passed = False
                    break
            elif op == ">":
                if not (current_val > compare_val):
                    all_passed = False
                    break
            elif op == "<=":
                if not (current_val <= compare_val):
                    all_passed = False
                    break
            elif op == ">=":
                if not (current_val >= compare_val):
                    all_passed = False
                    break
            
        if all_passed:
            close_p = current_bar['Close']
            atr = current_bar.get('ATR_14', close_p * 0.005)
            
            sl_atr = self.config.get("stop_loss_atr", 1.0)
            tp_atr = self.config.get("take_profit_atr", 2.0)
            
            signal_dict["signal"] = "BUY"
            signal_dict["reason"] = "Dynamic conditions met"
            signal_dict["stop_loss"] = close_p - (atr * sl_atr)
            signal_dict["target"] = close_p + (atr * tp_atr)
            signal_dict["conviction"] = 0.6
            return signal_dict
            
        signal_dict["reason"] = failed_reason or "Conditions not met"
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
