import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta
from services.backtesting import run_backtest

st.set_page_config(page_title="Backtesting | QuantEdge", layout="wide")

st.title("Strategy Backtesting")
st.markdown("Evaluate trading strategies on historical data with comprehensive performance metrics")

with st.sidebar:
    st.subheader("Backtest Configuration")
    strategy = st.selectbox(
        "Strategy",
        ["momentum", "mean_reversion", "ml_sentiment"],
        format_func=lambda x: {
            "momentum": "Momentum (RSI + MACD)",
            "mean_reversion": "Mean Reversion (Bollinger Bands)",
            "ml_sentiment": "ML Sentiment (FinBERT)",
        }.get(x, x),
    )
    symbol = st.text_input("Symbol", value="SPY").upper()
    col_s, col_e = st.columns(2)
    with col_s:
        start_date = st.date_input("Start", value=datetime(2021, 1, 1))
    with col_e:
        end_date = st.date_input("End", value=datetime(2023, 12, 31))

    initial_capital = st.number_input("Initial Capital ($)", min_value=1000.0, value=100000.0, step=1000.0)
    cash_at_risk = st.slider("Cash at Risk per Trade", 0.1, 1.0, 0.5, 0.05)

    st.subheader("Strategy Parameters")
    params = {"cash_at_risk": cash_at_risk}

    if strategy == "momentum":
        params["rsi_oversold"] = st.slider("RSI Oversold Threshold", 10, 40, 30)
        params["rsi_overbought"] = st.slider("RSI Overbought Threshold", 60, 90, 70)
    elif strategy == "mean_reversion":
        params["bb_std"] = st.slider("Bollinger Band Std Dev", 1.0, 3.0, 2.0, 0.1)
    elif strategy == "ml_sentiment":
        params["sentiment_threshold"] = st.slider("Sentiment Threshold", 0.5, 0.99, 0.7, 0.01)
        st.warning("ML Sentiment requires FinBERT model download on first run")

    run_btn = st.button("Run Backtest", use_container_width=True, type="primary")

if run_btn:
    if start_date >= end_date:
        st.error("Start date must be before end date")
    else:
        with st.spinner(f"Running {strategy} backtest on {symbol}..."):
            try:
                result = run_backtest(
                    strategy=strategy,
                    symbol=symbol,
                    start_date=str(start_date),
                    end_date=str(end_date),
                    initial_capital=initial_capital,
                    parameters=params,
                )
                st.session_state["last_backtest"] = result.to_dict()
                st.success("Backtest completed")
            except Exception as e:
                st.error(f"Backtest failed: {e}")

if "last_backtest" in st.session_state:
    res = st.session_state["last_backtest"]
    st.subheader("Performance Summary")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        ret_pct = res.get("total_return_pct", 0)
        st.metric("Total Return", f"{ret_pct:+.2f}%",
                  delta_color="normal" if ret_pct >= 0 else "inverse")
    with col2:
        st.metric("Final Equity", f"${res.get('final_equity', 0):,.2f}")
    with col3:
        st.metric("Sharpe Ratio", f"{res.get('sharpe_ratio', 0):.3f}")
    with col4:
        st.metric("Max Drawdown", f"{res.get('max_drawdown_pct', 0):.2f}%")

    col5, col6, col7, col8 = st.columns(4)
    with col5:
        st.metric("Sortino Ratio", f"{res.get('sortino_ratio', 0):.3f}")
    with col6:
        st.metric("Win Rate", f"{res.get('win_rate_pct', 0):.1f}%")
    with col7:
        st.metric("Profit Factor", f"{res.get('profit_factor', 0):.2f}")
    with col8:
        st.metric("Total Trades", res.get("total_trades", 0))

    tab1, tab2, tab3 = st.tabs(["Equity Curve", "Trade Analysis", "Trade Log"])

    with tab1:
        equity_curve_data = res.get("equity_curve", {})
        if equity_curve_data:
            dates = list(equity_curve_data.keys())
            values = list(equity_curve_data.values())
            eq_df = pd.DataFrame({"Date": pd.to_datetime(dates), "Equity": values})
            eq_df = eq_df.sort_values("Date")

            benchmark_start = eq_df["Equity"].iloc[0]

            fig_eq = go.Figure()
            fig_eq.add_trace(go.Scatter(
                x=eq_df["Date"],
                y=eq_df["Equity"],
                mode="lines",
                name="Strategy",
                line=dict(color="#89b4fa", width=2),
                fill="tozeroy",
                fillcolor="rgba(137,180,250,0.1)",
            ))
            fig_eq.add_hline(
                y=res.get("initial_capital", 100000),
                line_dash="dash",
                line_color="#6c7086",
                annotation_text="Initial Capital",
            )
            fig_eq.update_layout(
                title="Equity Curve",
                plot_bgcolor="#1e1e2e",
                paper_bgcolor="#181825",
                font_color="#cdd6f4",
                height=400,
                xaxis=dict(gridcolor="#313244"),
                yaxis=dict(gridcolor="#313244", tickprefix="$"),
            )
            st.plotly_chart(fig_eq, use_container_width=True)

            drawdown_series = (eq_df["Equity"] - eq_df["Equity"].cummax()) / eq_df["Equity"].cummax() * 100
            fig_dd = go.Figure()
            fig_dd.add_trace(go.Scatter(
                x=eq_df["Date"],
                y=drawdown_series,
                mode="lines",
                name="Drawdown",
                line=dict(color="#f38ba8", width=1.5),
                fill="tozeroy",
                fillcolor="rgba(243,139,168,0.2)",
            ))
            fig_dd.update_layout(
                title="Drawdown (%)",
                plot_bgcolor="#1e1e2e",
                paper_bgcolor="#181825",
                font_color="#cdd6f4",
                height=250,
                xaxis=dict(gridcolor="#313244"),
                yaxis=dict(gridcolor="#313244", ticksuffix="%"),
            )
            st.plotly_chart(fig_dd, use_container_width=True)

    with tab2:
        trades = res.get("trades", [])
        if trades:
            pnls = [t["pnl"] for t in trades]
            winning = [p for p in pnls if p > 0]
            losing = [p for p in pnls if p < 0]

            col_a, col_b = st.columns(2)
            with col_a:
                fig_pnl = go.Figure()
                colors = ["#a6e3a1" if p >= 0 else "#f38ba8" for p in pnls]
                fig_pnl.add_trace(go.Bar(
                    x=list(range(len(pnls))),
                    y=pnls,
                    marker_color=colors,
                    name="Trade P&L",
                ))
                fig_pnl.update_layout(
                    title="Individual Trade P&L",
                    plot_bgcolor="#1e1e2e",
                    paper_bgcolor="#181825",
                    font_color="#cdd6f4",
                    height=300,
                    yaxis=dict(gridcolor="#313244", tickprefix="$"),
                    xaxis=dict(gridcolor="#313244", title="Trade #"),
                )
                st.plotly_chart(fig_pnl, use_container_width=True)

            with col_b:
                win_count = len(winning)
                lose_count = len(losing)
                fig_pie = px.pie(
                    values=[win_count, lose_count],
                    names=["Winning", "Losing"],
                    color_discrete_sequence=["#a6e3a1", "#f38ba8"],
                    hole=0.4,
                    title="Win/Loss Ratio",
                )
                fig_pie.update_layout(
                    plot_bgcolor="#1e1e2e",
                    paper_bgcolor="#181825",
                    font_color="#cdd6f4",
                    height=300,
                )
                st.plotly_chart(fig_pie, use_container_width=True)

            extra_col1, extra_col2, extra_col3 = st.columns(3)
            with extra_col1:
                avg_win = sum(winning) / len(winning) if winning else 0
                st.metric("Avg Win", f"${avg_win:.2f}")
            with extra_col2:
                avg_loss = sum(losing) / len(losing) if losing else 0
                st.metric("Avg Loss", f"${avg_loss:.2f}")
            with extra_col3:
                expectancy = res.get("expectancy", 0)
                st.metric("Trade Expectancy", f"${expectancy:.2f}")

    with tab3:
        trades = res.get("trades", [])
        if trades:
            df_trades = pd.DataFrame(trades)
            if "pnl" in df_trades.columns:
                df_trades["pnl"] = df_trades["pnl"].apply(lambda x: f"${x:+.2f}")
            if "pnl_pct" in df_trades.columns:
                df_trades["pnl_pct"] = df_trades["pnl_pct"].apply(lambda x: f"{x:+.4f}%")
            st.dataframe(df_trades, use_container_width=True, hide_index=True)
        else:
            st.info("No trades were executed in this period")
else:
    st.info("Configure backtest parameters in the sidebar and click Run Backtest")
