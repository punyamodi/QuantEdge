import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from services.market_data import get_market_movers, get_multiple_quotes, fetch_ohlcv
from services.indicators import add_all_indicators
from services.sentiment import get_aggregate_sentiment
from services.market_data import get_news_headlines

st.set_page_config(page_title="Dashboard | QuantEdge", layout="wide")

st.title("Market Dashboard")
st.markdown("Real-time overview of market conditions and your watchlist")

@st.cache_data(ttl=300)
def load_market_data():
    return get_market_movers()

@st.cache_data(ttl=300)
def load_watchlist_quotes(symbols):
    return get_multiple_quotes(symbols)

tab1, tab2, tab3 = st.tabs(["Market Overview", "Watchlist", "Heatmap"])

with tab1:
    st.subheader("Market Indices")
    try:
        movers = load_market_data()
        indices = movers.get("indices", [])
        if indices:
            cols = st.columns(len(indices))
            for i, idx in enumerate(indices):
                with cols[i]:
                    name_map = {
                        "^GSPC": "S&P 500",
                        "^DJI": "Dow Jones",
                        "^IXIC": "NASDAQ",
                        "^RUT": "Russell 2000",
                    }
                    name = name_map.get(idx["symbol"], idx["symbol"])
                    st.metric(
                        label=name,
                        value=f"${idx['price']:,.2f}",
                        delta=f"{idx.get('change_pct', 0):+.2f}%",
                    )

        col_gain, col_lose = st.columns(2)
        with col_gain:
            st.subheader("Top Gainers")
            gainers = movers.get("gainers", [])
            if gainers:
                df_gain = pd.DataFrame(gainers)[["symbol", "price", "change_pct"]]
                df_gain.columns = ["Symbol", "Price", "Change %"]
                df_gain["Price"] = df_gain["Price"].apply(lambda x: f"${x:.2f}")
                df_gain["Change %"] = df_gain["Change %"].apply(lambda x: f"+{x:.2f}%")
                st.dataframe(df_gain, use_container_width=True, hide_index=True)

        with col_lose:
            st.subheader("Top Losers")
            losers = movers.get("losers", [])
            if losers:
                df_lose = pd.DataFrame(losers)[["symbol", "price", "change_pct"]]
                df_lose.columns = ["Symbol", "Price", "Change %"]
                df_lose["Price"] = df_lose["Price"].apply(lambda x: f"${x:.2f}")
                df_lose["Change %"] = df_lose["Change %"].apply(lambda x: f"{x:.2f}%")
                st.dataframe(df_lose, use_container_width=True, hide_index=True)
    except Exception as e:
        st.error(f"Failed to load market data: {e}")

with tab2:
    st.subheader("Watchlist")
    watchlist = st.session_state.get("watchlist", ["SPY", "AAPL", "MSFT", "GOOGL"])

    new_symbol = st.text_input("Add symbol to watchlist", placeholder="e.g. TSLA")
    if st.button("Add") and new_symbol:
        if new_symbol.upper() not in watchlist:
            st.session_state.watchlist.append(new_symbol.upper())
            st.rerun()

    try:
        quotes = load_watchlist_quotes(tuple(watchlist))
        if quotes:
            df_watch = pd.DataFrame(quotes)
            available_cols = [c for c in ["symbol", "price", "change", "change_pct", "volume", "market_cap"] if c in df_watch.columns]
            df_watch = df_watch[available_cols]

            def style_change(val):
                if isinstance(val, (int, float)):
                    if val > 0:
                        return "color: #a6e3a1"
                    elif val < 0:
                        return "color: #f38ba8"
                return ""

            if "change_pct" in df_watch.columns:
                st.dataframe(
                    df_watch.style.applymap(style_change, subset=["change_pct"]),
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.dataframe(df_watch, use_container_width=True, hide_index=True)
    except Exception as e:
        st.error(f"Failed to load watchlist: {e}")

with tab3:
    st.subheader("Sector Performance (YTD)")
    sector_etfs = {
        "Technology": "XLK",
        "Healthcare": "XLV",
        "Financials": "XLF",
        "Energy": "XLE",
        "Utilities": "XLU",
        "Consumer Disc.": "XLY",
        "Consumer Staples": "XLP",
        "Industrials": "XLI",
        "Materials": "XLB",
        "Real Estate": "XLRE",
    }
    try:
        sector_quotes = get_multiple_quotes(list(sector_etfs.values()))
        sector_data = []
        for i, (sector_name, etf) in enumerate(sector_etfs.items()):
            if i < len(sector_quotes):
                q = sector_quotes[i]
                sector_data.append({
                    "Sector": sector_name,
                    "ETF": etf,
                    "Change %": q.get("change_pct", 0),
                })
        if sector_data:
            df_sector = pd.DataFrame(sector_data)
            df_sector = df_sector.sort_values("Change %", ascending=True)
            fig = px.bar(
                df_sector,
                x="Change %",
                y="Sector",
                orientation="h",
                color="Change %",
                color_continuous_scale=["#f38ba8", "#fab387", "#a6e3a1"],
                title="Sector Performance Today",
            )
            fig.update_layout(
                plot_bgcolor="#1e1e2e",
                paper_bgcolor="#1e1e2e",
                font_color="#cdd6f4",
            )
            st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Failed to load sector data: {e}")
