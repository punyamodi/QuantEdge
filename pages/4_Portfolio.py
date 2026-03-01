import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from services.portfolio import get_account, get_positions, get_open_orders, is_connected
from services.market_data import fetch_ohlcv
from services.risk import calculate_sharpe_ratio, calculate_max_drawdown

st.set_page_config(page_title="Portfolio | QuantEdge", layout="wide")

st.title("Portfolio Management")
st.markdown("Live portfolio tracking and performance analytics")

connected = is_connected()

if not connected:
    st.warning(
        "Alpaca broker not connected. Configure your API credentials in Settings to view live portfolio data."
    )
    st.subheader("Portfolio Demo Mode")
    demo_positions = [
        {"symbol": "AAPL", "qty": 50, "avg_entry_price": 175.0, "current_price": 182.5, "market_value": 9125.0, "unrealized_pl": 375.0, "unrealized_plpc": 4.29, "side": "long", "cost_basis": 8750.0},
        {"symbol": "MSFT", "qty": 30, "avg_entry_price": 380.0, "current_price": 395.0, "market_value": 11850.0, "unrealized_pl": 450.0, "unrealized_plpc": 3.95, "side": "long", "cost_basis": 11400.0},
        {"symbol": "GOOGL", "qty": 20, "avg_entry_price": 140.0, "current_price": 137.5, "market_value": 2750.0, "unrealized_pl": -50.0, "unrealized_plpc": -1.79, "side": "long", "cost_basis": 2800.0},
        {"symbol": "NVDA", "qty": 25, "avg_entry_price": 480.0, "current_price": 510.0, "market_value": 12750.0, "unrealized_pl": 750.0, "unrealized_plpc": 6.25, "side": "long", "cost_basis": 12000.0},
    ]
    positions = demo_positions
    total_equity = 150000.0
    cash = 113525.0
    positions_value = 36475.0
else:
    account = get_account()
    positions = get_positions()
    total_equity = account.get("equity", 0) if account else 0
    cash = account.get("cash", 0) if account else 0
    positions_value = account.get("long_market_value", 0) if account else 0

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Equity", f"${total_equity:,.2f}")
with col2:
    st.metric("Cash Balance", f"${cash:,.2f}")
with col3:
    st.metric("Positions Value", f"${positions_value:,.2f}")
with col4:
    total_unrealized = sum(p.get("unrealized_pl", 0) for p in positions)
    color_dir = "normal" if total_unrealized >= 0 else "inverse"
    st.metric("Unrealized P&L", f"${total_unrealized:+,.2f}", delta_color=color_dir)

tab1, tab2, tab3 = st.tabs(["Positions", "Allocation", "Performance"])

with tab1:
    if positions:
        df_pos = pd.DataFrame(positions)
        display_cols = ["symbol", "qty", "avg_entry_price", "current_price", "market_value", "unrealized_pl", "unrealized_plpc"]
        available = [c for c in display_cols if c in df_pos.columns]
        df_display = df_pos[available].copy()

        rename_map = {
            "symbol": "Symbol",
            "qty": "Qty",
            "avg_entry_price": "Entry Price",
            "current_price": "Current Price",
            "market_value": "Market Value",
            "unrealized_pl": "Unrealized P&L",
            "unrealized_plpc": "P&L %",
        }
        df_display = df_display.rename(columns=rename_map)

        if "Entry Price" in df_display.columns:
            df_display["Entry Price"] = df_display["Entry Price"].apply(lambda x: f"${x:.2f}")
        if "Current Price" in df_display.columns:
            df_display["Current Price"] = df_display["Current Price"].apply(lambda x: f"${x:.2f}")
        if "Market Value" in df_display.columns:
            df_display["Market Value"] = df_display["Market Value"].apply(lambda x: f"${x:,.2f}")
        if "Unrealized P&L" in df_display.columns:
            df_display["Unrealized P&L"] = df_display["Unrealized P&L"].apply(lambda x: f"${x:+,.2f}")
        if "P&L %" in df_display.columns:
            df_display["P&L %"] = df_display["P&L %"].apply(lambda x: f"{x:+.2f}%")

        st.dataframe(df_display, use_container_width=True, hide_index=True)
    else:
        st.info("No open positions")

with tab2:
    if positions:
        alloc_data = []
        for p in positions:
            alloc_data.append({
                "symbol": p["symbol"],
                "value": p.get("market_value", 0),
            })

        if cash > 0:
            alloc_data.append({"symbol": "Cash", "value": cash})

        df_alloc = pd.DataFrame(alloc_data)
        fig_alloc = px.pie(
            df_alloc,
            values="value",
            names="symbol",
            title="Portfolio Allocation",
            hole=0.4,
            color_discrete_sequence=px.colors.sequential.Blues_r,
        )
        fig_alloc.update_layout(
            plot_bgcolor="#1e1e2e",
            paper_bgcolor="#181825",
            font_color="#cdd6f4",
            height=400,
        )
        st.plotly_chart(fig_alloc, use_container_width=True)

        df_bar = pd.DataFrame([
            {
                "Symbol": p["symbol"],
                "P&L %": p.get("unrealized_plpc", 0),
            }
            for p in positions
        ])
        fig_bar = px.bar(
            df_bar,
            x="Symbol",
            y="P&L %",
            title="Unrealized P&L by Position",
            color="P&L %",
            color_continuous_scale=["#f38ba8", "#a6e3a1"],
        )
        fig_bar.add_hline(y=0, line_dash="dash", line_color="#6c7086")
        fig_bar.update_layout(
            plot_bgcolor="#1e1e2e",
            paper_bgcolor="#181825",
            font_color="#cdd6f4",
            height=300,
        )
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info("No positions to display")

with tab3:
    st.subheader("Historical Performance by Symbol")
    if positions:
        perf_symbol = st.selectbox("Select symbol", [p["symbol"] for p in positions])
        perf_period = st.selectbox("Period", ["3mo", "6mo", "1y", "2y"])
        try:
            hist = fetch_ohlcv(perf_symbol, period=perf_period)
            if hist is not None and len(hist) > 0:
                returns = hist["Close"].pct_change().dropna()
                sharpe = calculate_sharpe_ratio(returns)
                max_dd = calculate_max_drawdown(hist["Close"]) * 100
                total_ret = (hist["Close"].iloc[-1] / hist["Close"].iloc[0] - 1) * 100

                mc1, mc2, mc3 = st.columns(3)
                with mc1:
                    st.metric("Total Return", f"{total_ret:+.2f}%")
                with mc2:
                    st.metric("Sharpe Ratio", f"{sharpe:.3f}")
                with mc3:
                    st.metric("Max Drawdown", f"{max_dd:.2f}%")

                fig_hist = go.Figure()
                fig_hist.add_trace(go.Scatter(
                    x=hist.index,
                    y=hist["Close"],
                    mode="lines",
                    line=dict(color="#89b4fa", width=1.5),
                    name=perf_symbol,
                ))
                fig_hist.update_layout(
                    title=f"{perf_symbol} Price History ({perf_period})",
                    plot_bgcolor="#1e1e2e",
                    paper_bgcolor="#181825",
                    font_color="#cdd6f4",
                    height=350,
                    xaxis=dict(gridcolor="#313244"),
                    yaxis=dict(gridcolor="#313244", tickprefix="$"),
                )
                st.plotly_chart(fig_hist, use_container_width=True)
        except Exception as e:
            st.error(f"Failed to load performance data: {e}")
