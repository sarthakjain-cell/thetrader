import pandas as pd
from abc import ABC, abstractmethod

class BaseStrategy(ABC):
    def __init__(self, strategy_id: str, name: str):
        self.strategy_id = strategy_id
        self.name = name
        self.params = self.get_default_parameters()

    def get_default_parameters(self) -> dict:
        """Override this to return default parameters for optimization."""
        return {}
        
    def set_parameters(self, params: dict):
        """Inject optimized parameters into the strategy."""
        self.params.update(params)

    @abstractmethod
    def evaluate(self, symbol: str, current_bar: pd.Series, context: dict) -> dict:
        """
        Evaluate the pre-computed current_bar (which includes features) and return a trading signal.
        
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
    def manage_position(self, symbol: str, current_position: dict, current_bar: pd.Series) -> dict:
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
