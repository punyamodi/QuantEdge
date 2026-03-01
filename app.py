import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st

st.set_page_config(
    page_title="QuantEdge",
    page_icon="assets/favicon.ico" if os.path.exists("assets/favicon.ico") else None,
    layout="wide",
    initial_sidebar_state="expanded",
)

if "alpaca_connected" not in st.session_state:
    st.session_state.alpaca_connected = False
if "watchlist" not in st.session_state:
    st.session_state.watchlist = ["SPY", "AAPL", "MSFT", "GOOGL", "AMZN"]
if "backtest_results" not in st.session_state:
    st.session_state.backtest_results = {}
if "settings" not in st.session_state:
    st.session_state.settings = {
        "default_symbol": "SPY",
        "cash_at_risk": 0.5,
        "initial_capital": 100000.0,
        "sentiment_threshold": 0.7,
        "take_profit_pct": 0.15,
        "stop_loss_pct": 0.05,
    }

st.markdown(
    """
    <style>
    .metric-card {
        background-color: #1e1e2e;
        border-radius: 10px;
        padding: 20px;
        margin: 5px;
        border: 1px solid #313244;
    }
    .positive { color: #a6e3a1; }
    .negative { color: #f38ba8; }
    .neutral { color: #89b4fa; }
    .stMetric { background-color: transparent; }
    div[data-testid="stSidebarContent"] { background-color: #181825; }
    .sidebar-title { font-size: 24px; font-weight: bold; color: #cdd6f4; }
    </style>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown('<div class="sidebar-title">QuantEdge</div>', unsafe_allow_html=True)
    st.markdown("*Quantitative Trading Platform*")
    st.divider()
    st.markdown("**Navigation**")
    st.page_link("app.py", label="Home", icon="🏠")
    st.page_link("pages/1_Dashboard.py", label="Dashboard", icon="📊")
    st.page_link("pages/2_Market_Analysis.py", label="Market Analysis", icon="📈")
    st.page_link("pages/3_Backtesting.py", label="Backtesting", icon="🔄")
    st.page_link("pages/4_Portfolio.py", label="Portfolio", icon="💼")
    st.page_link("pages/5_Live_Trading.py", label="Live Trading", icon="⚡")
    st.page_link("pages/6_Settings.py", label="Settings", icon="⚙️")
    st.divider()
    from services.portfolio import is_connected
    connected = is_connected()
    status_color = "green" if connected else "red"
    status_text = "Connected" if connected else "Disconnected"
    st.markdown(f"**Broker:** :{status_color}[{status_text}]")

st.title("QuantEdge — Quantitative Trading Platform")
st.markdown(
    """
    A professional-grade quantitative trading system combining machine learning sentiment analysis,
    technical indicators, and algorithmic strategies for systematic market participation.
    """
)

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(
        """
        <div class="metric-card">
            <h4>Market Analysis</h4>
            <p>Real-time price data with RSI, MACD, Bollinger Bands and 10+ indicators</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col2:
    st.markdown(
        """
        <div class="metric-card">
            <h4>ML Sentiment</h4>
            <p>FinBERT-powered news sentiment analysis for informed trading decisions</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col3:
    st.markdown(
        """
        <div class="metric-card">
            <h4>Backtesting</h4>
            <p>Test strategies on historical data with Sharpe, Sortino and drawdown metrics</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col4:
    st.markdown(
        """
        <div class="metric-card">
            <h4>Live Trading</h4>
            <p>Automated trading via Alpaca with bracket orders and risk management</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.subheader("Quick Market Overview")
try:
    from services.market_data import get_multiple_quotes
    symbols = ["SPY", "QQQ", "DIA", "IWM"]
    quotes = get_multiple_quotes(symbols)
    cols = st.columns(len(quotes))
    for i, q in enumerate(quotes):
        with cols[i]:
            change_pct = q.get("change_pct", 0)
            delta_color = "normal" if change_pct >= 0 else "inverse"
            st.metric(
                label=q["symbol"],
                value=f"${q['price']:.2f}",
                delta=f"{change_pct:+.2f}%",
                delta_color="normal",
            )
except Exception as e:
    st.info("Configure your environment and refresh to see live market data.")

st.subheader("Get Started")
st.markdown(
    """
    1. Navigate to **Settings** to configure your Alpaca API credentials
    2. Go to **Market Analysis** to explore stocks with technical indicators
    3. Use **Backtesting** to evaluate strategies on historical data
    4. Monitor your portfolio in **Portfolio** once connected
    5. Enable **Live Trading** to run automated strategies
    """
)
