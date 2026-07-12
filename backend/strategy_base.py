import pandas as pd
from abc import ABC, abstractmethod

class BaseStrategy(ABC):
    def __init__(self, strategy_id: str, name: str):
        self.strategy_id = strategy_id
        self.name = name

    @abstractmethod
    def evaluate(self, symbol: str, df: pd.DataFrame, context: dict) -> dict:
        """
        Evaluate the latest market data and return a trading signal.
        context can contain global macro alerts or regimes.
        
        Returns:
        {
            "signal": "BUY" | "SELL" | "HOLD" | "VETO",
            "reason": str,
            "stop_loss": float or None,
            "target": float or None,
            "conviction": float (0 to 1)
        }
        """
        pass
    
    @abstractmethod
    def manage_position(self, symbol: str, current_position: dict, df: pd.DataFrame) -> dict:
        """
        Manage an open position.
        
        Returns:
        {
            "action": "CLOSE" | "HOLD" | "UPDATE_STOP",
            "reason": str,
            "new_stop": float or None,
            "exit_price": float or None (if CLOSE)
        }
        """
        pass
