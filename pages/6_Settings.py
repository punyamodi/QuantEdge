import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from core.config import settings

st.set_page_config(page_title="Settings | QuantEdge", layout="wide")

st.title("Settings")
st.markdown("Configure your API credentials and application preferences")

tab1, tab2, tab3 = st.tabs(["Broker Credentials", "Strategy Defaults", "About"])

with tab1:
    st.subheader("Alpaca API Configuration")
    st.markdown(
        "Get your API keys from [Alpaca Markets](https://alpaca.markets). "
        "Use paper trading keys for testing."
    )

    with st.form("credentials_form"):
        api_key = st.text_input(
            "API Key",
            value=os.environ.get("ALPACA_API_KEY", ""),
            type="password",
            placeholder="Enter your Alpaca API key",
        )
        api_secret = st.text_input(
            "API Secret",
            value=os.environ.get("ALPACA_API_SECRET", ""),
            type="password",
            placeholder="Enter your Alpaca API secret",
        )
        base_url = st.selectbox(
            "Environment",
            ["https://paper-api.alpaca.markets", "https://api.alpaca.markets"],
            index=0,
            format_func=lambda x: "Paper Trading" if "paper" in x else "Live Trading",
        )
        save_btn = st.form_submit_button("Save & Test Connection")

    if save_btn:
        os.environ["ALPACA_API_KEY"] = api_key
        os.environ["ALPACA_API_SECRET"] = api_secret
        os.environ["ALPACA_BASE_URL"] = base_url

        with st.spinner("Testing connection..."):
            try:
                from alpaca_trade_api import REST
                client = REST(base_url=base_url, key_id=api_key, secret_key=api_secret)
                account = client.get_account()
                st.success(f"Connected! Account #{account.account_number} | Equity: ${float(account.equity):,.2f}")
                st.session_state.alpaca_connected = True
            except ImportError:
                st.error("alpaca-trade-api package not installed. Run: pip install alpaca-trade-api")
            except Exception as e:
                st.error(f"Connection failed: {e}")
                st.session_state.alpaca_connected = False

    st.divider()
    st.subheader("Environment File Setup")
    st.markdown("Create a `.env` file in the project root with these variables:")
    st.code(
        """ALPACA_API_KEY=your_api_key_here
ALPACA_API_SECRET=your_api_secret_here
ALPACA_BASE_URL=https://paper-api.alpaca.markets
ALPACA_PAPER=true""",
        language="bash",
    )

with tab2:
    st.subheader("Default Strategy Parameters")
    current = st.session_state.get("settings", {})

    with st.form("strategy_defaults_form"):
        default_symbol = st.text_input("Default Symbol", value=current.get("default_symbol", "SPY"))
        initial_capital = st.number_input(
            "Default Initial Capital ($)",
            min_value=1000.0,
            value=float(current.get("initial_capital", 100000.0)),
            step=1000.0,
        )
        cash_at_risk = st.slider(
            "Default Cash at Risk per Trade",
            0.05, 1.0,
            float(current.get("cash_at_risk", 0.5)),
            0.05,
        )
        sentiment_threshold = st.slider(
            "Sentiment Confidence Threshold",
            0.5, 0.99,
            float(current.get("sentiment_threshold", 0.7)),
            0.01,
        )
        take_profit_pct = st.slider(
            "Take Profit %",
            1.0, 50.0,
            float(current.get("take_profit_pct", 15.0)),
            1.0,
        )
        stop_loss_pct = st.slider(
            "Stop Loss %",
            1.0, 20.0,
            float(current.get("stop_loss_pct", 5.0)),
            0.5,
        )
        save_defaults = st.form_submit_button("Save Defaults")

    if save_defaults:
        st.session_state.settings = {
            "default_symbol": default_symbol.upper(),
            "initial_capital": initial_capital,
            "cash_at_risk": cash_at_risk,
            "sentiment_threshold": sentiment_threshold,
            "take_profit_pct": take_profit_pct,
            "stop_loss_pct": stop_loss_pct,
        }
        st.success("Default settings saved for this session")

with tab3:
    st.subheader("About QuantEdge")
    st.markdown(
        """
        **QuantEdge** is a professional quantitative trading platform combining:

        - **FinBERT** NLP model for financial news sentiment analysis
        - **Technical indicators** (RSI, MACD, Bollinger Bands, Stochastics, ATR, OBV, and more)
        - **Three built-in strategies**: Momentum, Mean Reversion, ML Sentiment
        - **Comprehensive backtesting** with Sharpe, Sortino, Calmar ratios and drawdown analysis
        - **Live trading** via Alpaca Markets API with bracket orders
        - **Real-time market data** via yfinance

        **Tech Stack:**
        - Python 3.10+
        - Streamlit (UI)
        - FastAPI (REST API)
        - Transformers + PyTorch (FinBERT)
        - Plotly (Charts)
        - SQLAlchemy + SQLite (Data persistence)
        - yfinance (Market data)
        - Alpaca Trade API (Live trading)

        **GitHub:** [QuantEdge Repository](https://github.com/punyamodi/QuantEdge)
        """
    )

    st.subheader("System Status")
    col1, col2, col3 = st.columns(3)
    with col1:
        try:
            import yfinance
            st.success("yfinance: Available")
        except ImportError:
            st.error("yfinance: Not installed")
    with col2:
        try:
            import transformers
            st.success("Transformers: Available")
        except ImportError:
            st.error("Transformers: Not installed")
    with col3:
        try:
            import alpaca_trade_api
            st.success("Alpaca API: Available")
        except ImportError:
            st.warning("Alpaca API: Not installed")
