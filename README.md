# QuantEdge — Quantitative Trading Platform

<img width="1076" alt="image" src="https://github.com/punyamodi/Trading_Bot/assets/68418104/5671134e-2ac8-42ce-9d6c-0408ce20590e">

A professional-grade quantitative trading system combining FinBERT sentiment analysis, technical indicators, and algorithmic strategies for systematic market participation. Features a full Streamlit dashboard, FastAPI REST backend, comprehensive backtesting engine, and live trading via Alpaca Markets.

---

## Features

**Market Analysis**
- Real-time price data and candlestick charts via yfinance
- 12+ technical indicators: RSI, MACD, Bollinger Bands, Stochastics, ATR, OBV, Williams %R, CCI, VWAP
- Moving averages: SMA 20/50/200, EMA 9/21
- Automated signal detection with bullish/bearish classification
- Sector performance heatmap

**ML Sentiment Analysis**
- FinBERT (ProsusAI/finbert) for financial news NLP
- Per-headline and aggregate sentiment scoring
- Sentiment breakdown chart with positive/negative/neutral distribution
- News feed integration via yfinance

**Backtesting Engine**
- Three built-in strategies: Momentum, Mean Reversion, ML Sentiment
- Configurable parameters: RSI thresholds, Bollinger Band width, sentiment threshold
- Performance metrics: Sharpe ratio, Sortino ratio, Calmar ratio, max drawdown, win rate, profit factor, trade expectancy
- Interactive equity curve and drawdown charts
- Full trade log with entry/exit details

**Portfolio Management**
- Live position tracking via Alpaca API
- Unrealized P&L by position
- Portfolio allocation pie chart
- Historical performance per symbol

**Live Trading**
- Manual order placement with bracket orders (take profit + stop loss)
- Sentiment-driven automated strategy runner
- Open order management and cancellation
- Paper and live trading support

**REST API (FastAPI)**
- `/api/market/quote/{symbol}` — real-time quote
- `/api/market/indicators/{symbol}` — full indicator set
- `/api/market/sentiment/{symbol}` — FinBERT sentiment
- `/api/backtest/run` — async backtest execution
- `/api/portfolio/positions` — live positions
- `/api/trading/order` — order placement

---

## Architecture

```
quantedge/
├── app.py                  # Streamlit main entry point
├── pages/
│   ├── 1_Dashboard.py      # Market overview and watchlist
│   ├── 2_Market_Analysis.py # Charts and technical analysis
│   ├── 3_Backtesting.py    # Strategy backtesting
│   ├── 4_Portfolio.py      # Portfolio and positions
│   ├── 5_Live_Trading.py   # Order placement and automation
│   └── 6_Settings.py       # API credentials and defaults
├── api/
│   ├── main.py             # FastAPI application
│   └── routes/             # market, portfolio, backtest, trading
├── core/
│   ├── config.py           # Pydantic settings
│   └── database.py         # SQLAlchemy engine
├── models/
│   ├── orm.py              # Database models
│   └── schemas.py          # Pydantic schemas
├── services/
│   ├── market_data.py      # yfinance data fetching
│   ├── sentiment.py        # FinBERT inference
│   ├── indicators.py       # Technical analysis
│   ├── backtesting.py      # Backtesting engine
│   ├── risk.py             # Risk metrics
│   └── portfolio.py        # Alpaca broker integration
├── strategies/
│   ├── base.py             # Abstract base strategy
│   ├── momentum.py         # RSI + MACD momentum
│   ├── mean_reversion.py   # Bollinger Band reversion
│   └── ml_sentiment.py     # FinBERT sentiment strategy
└── tests/
    ├── test_indicators.py
    └── test_risk.py
```

---

## Installation

**Prerequisites:** Python 3.10+

```bash
git clone https://github.com/punyamodi/QuantEdge.git
cd QuantEdge
pip install -r requirements.txt
```

**Environment Setup**

Copy `.env.example` to `.env` and add your credentials:

```bash
cp .env.example .env
```

```env
ALPACA_API_KEY=your_api_key
ALPACA_API_SECRET=your_api_secret
ALPACA_BASE_URL=https://paper-api.alpaca.markets
```

Get free paper trading API keys at [alpaca.markets](https://alpaca.markets).

---

## Usage

**Launch the UI (Streamlit dashboard)**

```bash
streamlit run app.py
```

Opens at `http://localhost:8501`

**Launch the REST API**

```bash
python run.py api
```

API runs at `http://localhost:8000` with interactive docs at `/docs`

**Launch both**

```bash
python run.py both
```

**Run tests**

```bash
pytest tests/ -v
```

---

## Strategies

| Strategy | Signal Sources | Key Parameters |
|---|---|---|
| Momentum | RSI + MACD crossover | RSI oversold/overbought, volume confirmation |
| Mean Reversion | Bollinger Bands | Band width, RSI filter, take profit at mid-band |
| ML Sentiment | FinBERT news NLP | Confidence threshold, technical confirmation |

---

## Risk Metrics

| Metric | Description |
|---|---|
| Sharpe Ratio | Risk-adjusted return vs risk-free rate |
| Sortino Ratio | Sharpe using only downside volatility |
| Calmar Ratio | Annual return divided by max drawdown |
| Max Drawdown | Largest peak-to-trough decline |
| Win Rate | Percentage of profitable trades |
| Profit Factor | Gross profit divided by gross loss |
| VaR (95%) | Value at Risk at 95% confidence |
| CVaR | Conditional VaR (expected shortfall) |

---

## Backtesting Example

```python
from services.backtesting import run_backtest

result = run_backtest(
    strategy="momentum",
    symbol="SPY",
    start_date="2021-01-01",
    end_date="2023-12-31",
    initial_capital=100000.0,
    parameters={
        "rsi_oversold": 30,
        "rsi_overbought": 70,
        "cash_at_risk": 0.5,
    }
)

print(result.to_dict())
```

---

## Disclaimer

This software is for educational and research purposes only. It does not constitute financial advice. Trading involves substantial risk of loss. Past performance of backtested strategies does not guarantee future results. Always test with paper trading before using real capital.

---

## Legacy Code

The original MLTrader script using Lumibot is preserved on the [`legacy`](https://github.com/punyamodi/QuantEdge/tree/legacy) branch.
