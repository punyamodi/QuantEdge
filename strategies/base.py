from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import pandas as pd


class BaseStrategy(ABC):
    def __init__(self, symbol: str, parameters: Optional[Dict[str, Any]] = None):
        self.symbol = symbol
        self.parameters = parameters or {}

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        pass

    @abstractmethod
    def get_default_parameters(self) -> Dict[str, Any]:
        pass

    def validate_parameters(self) -> bool:
        defaults = self.get_default_parameters()
        for key, value in defaults.items():
            if key not in self.parameters:
                self.parameters[key] = value
        return True

    def get_description(self) -> str:
        return f"Strategy: {self.name} for {self.symbol}"
