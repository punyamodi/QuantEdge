import pandas as pd
from typing import Dict, Any, List, Optional
from strategies.base import BaseStrategy
from services.indicators import add_all_indicators
from services.sentiment import estimate_sentiment
from services.market_data import get_news_headlines


class MLSentimentStrategy(BaseStrategy):
    @property
    def name(self) -> str:
        return "ML Sentiment"

    def get_default_parameters(self) -> Dict[str, Any]:
        return {
            "sentiment_threshold": 0.7,
            "cash_at_risk": 0.5,
            "take_profit_pct": 0.20,
            "stop_loss_pct": 0.05,
            "use_technical_confirmation": True,
            "rsi_filter_min": 25.0,
            "rsi_filter_max": 75.0,
        }

    def analyze_current_sentiment(self) -> Dict[str, Any]:
        headlines = get_news_headlines(self.symbol)
        if not headlines:
            return {"sentiment": "neutral", "probability": 0.0, "headline_count": 0}
        probability, sentiment = estimate_sentiment(headlines)
        return {
            "sentiment": sentiment,
            "probability": float(probability),
            "headline_count": len(headlines),
            "headlines": headlines[:5],
        }

    def generate_signals(self, df: pd.DataFrame, sentiment_map: Optional[Dict] = None) -> pd.DataFrame:
        self.validate_parameters()
        data = add_all_indicators(df.copy())
        data["signal"] = 0
        data["sentiment"] = "neutral"
        data["sentiment_prob"] = 0.0

        threshold = self.parameters["sentiment_threshold"]
        rsi_min = self.parameters["rsi_filter_min"]
        rsi_max = self.parameters["rsi_filter_max"]

        if sentiment_map:
            for date_str, sent_info in sentiment_map.items():
                try:
                    mask = data.index.strftime("%Y-%m-%d") == date_str
                    sentiment = sent_info.get("sentiment", "neutral")
                    probability = sent_info.get("probability", 0.0)
                    data.loc[mask, "sentiment"] = sentiment
                    data.loc[mask, "sentiment_prob"] = probability

                    if probability > threshold:
                        if self.parameters.get("use_technical_confirmation"):
                            if sentiment == "positive":
                                rsi_ok = data.loc[mask, "rsi"] < rsi_max
                                data.loc[mask & rsi_ok, "signal"] = 1
                            elif sentiment == "negative":
                                rsi_ok = data.loc[mask, "rsi"] > rsi_min
                                data.loc[mask & rsi_ok, "signal"] = -1
                        else:
                            if sentiment == "positive":
                                data.loc[mask, "signal"] = 1
                            elif sentiment == "negative":
                                data.loc[mask, "signal"] = -1
                except Exception:
                    continue

        return data

    def get_description(self) -> str:
        return (
            "ML-based sentiment strategy using FinBERT for news analysis. "
            "Buys on positive sentiment with technical confirmation. "
            "Uses RSI and moving averages as filters."
        )
