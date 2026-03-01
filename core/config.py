import os
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    alpaca_api_key: str = Field(default="", env="ALPACA_API_KEY")
    alpaca_api_secret: str = Field(default="", env="ALPACA_API_SECRET")
    alpaca_base_url: str = Field(
        default="https://paper-api.alpaca.markets", env="ALPACA_BASE_URL"
    )
    alpaca_paper: bool = Field(default=True, env="ALPACA_PAPER")

    database_url: str = Field(default="sqlite:///./quantedge.db", env="DATABASE_URL")

    finbert_model: str = Field(default="ProsusAI/finbert", env="FINBERT_MODEL")
    use_gpu: bool = Field(default=False, env="USE_GPU")

    default_symbol: str = Field(default="SPY", env="DEFAULT_SYMBOL")
    default_cash_at_risk: float = Field(default=0.02, env="DEFAULT_CASH_AT_RISK")
    default_initial_capital: float = Field(
        default=100000.0, env="DEFAULT_INITIAL_CAPITAL"
    )

    sentiment_threshold: float = Field(default=0.7, env="SENTIMENT_THRESHOLD")
    take_profit_multiplier: float = Field(default=1.20, env="TAKE_PROFIT_MULTIPLIER")
    stop_loss_multiplier: float = Field(default=0.95, env="STOP_LOSS_MULTIPLIER")

    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    streamlit_port: int = Field(default=8501, env="STREAMLIT_PORT")

    log_level: str = Field(default="INFO", env="LOG_LEVEL")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


settings = Settings()
