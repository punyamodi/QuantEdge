import pandas as pd
from typing import Dict, Any
from strategies.base import BaseStrategy
from services.indicators import add_all_indicators


class MeanReversionStrategy(BaseStrategy):
    @property
    def name(self) -> str:
        return "Mean Reversion"

    def get_default_parameters(self) -> Dict[str, Any]:
        return {
            "bb_period": 20,
            "bb_std": 2.0,
            "rsi_low": 35.0,
            "rsi_high": 65.0,
            "cash_at_risk": 0.5,
            "take_profit_at_mid": True,
            "stop_loss_pct": 0.05,
        }

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        self.validate_parameters()
        data = add_all_indicators(df.copy())
        data["signal"] = 0

        bb_std = self.parameters["bb_std"]
        rsi_low = self.parameters["rsi_low"]
        rsi_high = self.parameters["rsi_high"]

        buy_mask = (
            (data["Close"] < data["bb_lower"])
            & (data["rsi"] < rsi_high)
        )

        sell_mask = (
            (data["Close"] > data["bb_upper"])
            & (data["rsi"] > rsi_low)
        )

        data.loc[buy_mask, "signal"] = 1
        data.loc[sell_mask, "signal"] = -1

        data["bb_position"] = (data["Close"] - data["bb_lower"]) / (
            data["bb_upper"] - data["bb_lower"]
        )
        data["bb_position"] = data["bb_position"].clip(0, 1)

        return data

    def get_description(self) -> str:
        return (
            "Mean reversion strategy using Bollinger Bands. "
            "Buys when price drops below lower band and sells at the middle band. "
            "Uses RSI as confirmation filter."
        )
