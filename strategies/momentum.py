import pandas as pd
from typing import Dict, Any, Optional
from strategies.base import BaseStrategy
from services.indicators import add_all_indicators


class MomentumStrategy(BaseStrategy):
    @property
    def name(self) -> str:
        return "Momentum"

    def get_default_parameters(self) -> Dict[str, Any]:
        return {
            "rsi_oversold": 30.0,
            "rsi_overbought": 70.0,
            "macd_fast": 12,
            "macd_slow": 26,
            "macd_signal": 9,
            "cash_at_risk": 0.5,
            "take_profit_pct": 0.15,
            "stop_loss_pct": 0.07,
            "require_volume_confirm": True,
        }

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        self.validate_parameters()
        data = add_all_indicators(df.copy())
        data["signal"] = 0

        rsi_oversold = self.parameters["rsi_oversold"]
        rsi_overbought = self.parameters["rsi_overbought"]

        buy_mask = (
            (data["rsi"] < rsi_oversold)
            & (data["macd"] > data["macd_signal"])
            & (data["Close"] > data["sma_20"])
        )

        sell_mask = (
            (data["rsi"] > rsi_overbought)
            & (data["macd"] < data["macd_signal"])
        )

        if self.parameters.get("require_volume_confirm") and "Volume" in data.columns:
            avg_volume = data["Volume"].rolling(20).mean()
            buy_mask = buy_mask & (data["Volume"] > avg_volume)

        data.loc[buy_mask, "signal"] = 1
        data.loc[sell_mask, "signal"] = -1

        data["signal_strength"] = 0.0
        for i in range(len(data)):
            row = data.iloc[i]
            if pd.isna(row["rsi"]) or pd.isna(row["macd"]):
                continue
            score = 0.0
            if row["rsi"] < rsi_oversold:
                score += (rsi_oversold - row["rsi"]) / rsi_oversold
            if row["macd"] > row["macd_signal"]:
                score += abs(row["macd"] - row["macd_signal"])
            data.iloc[i, data.columns.get_loc("signal_strength")] = score

        return data

    def get_description(self) -> str:
        return (
            "Momentum strategy using RSI and MACD crossovers. "
            "Buys when RSI is oversold and MACD is bullish. "
            "Sells when RSI is overbought and MACD turns bearish."
        )
