import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from services.market_data import fetch_ohlcv, get_quote, get_news_headlines
from services.indicators import add_all_indicators, get_signal_summary
from services.sentiment import get_aggregate_sentiment

st.set_page_config(page_title="Market Analysis | QuantEdge", layout="wide")

st.title("Market Analysis")
st.markdown("Technical analysis with indicators and sentiment scoring")

with st.sidebar:
    st.subheader("Symbol Settings")
    symbol = st.text_input("Symbol", value="SPY").upper()
    period = st.selectbox("Period", ["1mo", "3mo", "6mo", "1y", "2y", "5y"], index=3)
    interval = st.selectbox("Interval", ["1d", "1wk", "1mo"], index=0)
    show_volume = st.checkbox("Show Volume", value=True)
    show_bollinger = st.checkbox("Bollinger Bands", value=True)
    show_sma = st.checkbox("Moving Averages", value=True)
    analyze_btn = st.button("Analyze", use_container_width=True)

@st.cache_data(ttl=180)
def load_analysis_data(sym, per, inter):
    df = fetch_ohlcv(sym, period=per, interval=inter)
    if df is None or len(df) < 20:
        return None, None, None
    df_with_ind = add_all_indicators(df.copy())
    signals = get_signal_summary(df_with_ind)
    try:
        quote = get_quote(sym)
    except Exception:
        quote = {}
    return df_with_ind, signals, quote

df, signals, quote = load_analysis_data(symbol, period, interval)

if df is not None and quote:
    price = quote.get("price", 0)
    change_pct = quote.get("change_pct", 0)

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Price", f"${price:.2f}", f"{change_pct:+.2f}%")
    with col2:
        st.metric("52W High", f"${quote.get('week_52_high', 0):.2f}")
    with col3:
        st.metric("52W Low", f"${quote.get('week_52_low', 0):.2f}")
    with col4:
        latest_rsi = df["rsi"].dropna().iloc[-1] if "rsi" in df.columns and len(df["rsi"].dropna()) > 0 else 0
        rsi_label = "Overbought" if latest_rsi > 70 else ("Oversold" if latest_rsi < 30 else "Neutral")
        st.metric("RSI (14)", f"{latest_rsi:.1f}", rsi_label)
    with col5:
        latest_atr = df["atr"].dropna().iloc[-1] if "atr" in df.columns and len(df["atr"].dropna()) > 0 else 0
        st.metric("ATR (14)", f"${latest_atr:.2f}")

    chart_rows = 3 if show_volume else 2
    row_heights = [0.6, 0.2, 0.2] if show_volume else [0.7, 0.3]
    subplot_titles = ["Price & Indicators", "MACD", "Volume & RSI"] if show_volume else ["Price & Indicators", "MACD"]

    fig = make_subplots(
        rows=chart_rows,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        row_heights=row_heights,
        subplot_titles=subplot_titles,
    )

    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df["Open"],
            high=df["High"],
            low=df["Low"],
            close=df["Close"],
            name="OHLC",
            increasing_line_color="#a6e3a1",
            decreasing_line_color="#f38ba8",
        ),
        row=1, col=1,
    )

    if show_bollinger and "bb_upper" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df["bb_upper"], name="BB Upper", line=dict(color="#89dceb", width=1, dash="dot")), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df["bb_mid"], name="BB Mid", line=dict(color="#74c7ec", width=1)), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df["bb_lower"], name="BB Lower", line=dict(color="#89dceb", width=1, dash="dot"), fill="tonexty", fillcolor="rgba(137,220,235,0.05)"), row=1, col=1)

    if show_sma and "sma_20" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df["sma_20"], name="SMA 20", line=dict(color="#f9e2af", width=1)), row=1, col=1)
    if show_sma and "sma_50" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df["sma_50"], name="SMA 50", line=dict(color="#fab387", width=1)), row=1, col=1)
    if show_sma and "sma_200" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df["sma_200"], name="SMA 200", line=dict(color="#cba6f7", width=1.5)), row=1, col=1)

    if "macd" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df["macd"], name="MACD", line=dict(color="#89b4fa", width=1.5)), row=2, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df["macd_signal"], name="Signal", line=dict(color="#f38ba8", width=1.5)), row=2, col=1)
        hist = df["macd_hist"]
        colors = ["#a6e3a1" if v >= 0 else "#f38ba8" for v in hist]
        fig.add_trace(go.Bar(x=df.index, y=hist, name="Histogram", marker_color=colors, opacity=0.7), row=2, col=1)

    if show_volume and "Volume" in df.columns:
        vol_colors = ["#a6e3a1" if df["Close"].iloc[i] >= df["Open"].iloc[i] else "#f38ba8" for i in range(len(df))]
        fig.add_trace(go.Bar(x=df.index, y=df["Volume"], name="Volume", marker_color=vol_colors, opacity=0.7), row=3, col=1)

    fig.update_layout(
        height=700,
        plot_bgcolor="#1e1e2e",
        paper_bgcolor="#181825",
        font=dict(color="#cdd6f4"),
        showlegend=True,
        legend=dict(bgcolor="#1e1e2e", bordercolor="#313244"),
        xaxis_rangeslider_visible=False,
    )
    fig.update_xaxes(gridcolor="#313244", showgrid=True)
    fig.update_yaxes(gridcolor="#313244", showgrid=True)

    st.plotly_chart(fig, use_container_width=True)

    col_signals, col_sentiment = st.columns(2)
    with col_signals:
        st.subheader("Technical Signals")
        if signals:
            for indicator, info in signals.items():
                signal_val = info.get("signal", "")
                color = "green" if "bullish" in signal_val or "oversold" in signal_val or "golden" in signal_val else (
                    "red" if "bearish" in signal_val or "overbought" in signal_val or "death" in signal_val else "blue"
                )
                st.markdown(f"**{indicator.upper()}**: :{color}[{signal_val.replace('_', ' ').title()}]")
        else:
            st.info("Insufficient data for signal analysis")

    with col_sentiment:
        st.subheader("News Sentiment")
        try:
            with st.spinner("Analyzing news..."):
                headlines = get_news_headlines(symbol)
                if headlines:
                    result = get_aggregate_sentiment(headlines[:10])
                    sentiment = result["sentiment"]
                    prob = result["probability"]
                    color_map = {"positive": "green", "negative": "red", "neutral": "blue"}
                    color = color_map.get(sentiment, "blue")
                    st.markdown(f"**Overall:** :{color}[{sentiment.upper()}] ({prob:.1%} confidence)")
                    breakdown = result.get("breakdown", {})
                    if breakdown:
                        import plotly.express as px
                        fig_sent = px.pie(
                            values=list(breakdown.values()),
                            names=list(breakdown.keys()),
                            color_discrete_sequence=["#a6e3a1", "#f38ba8", "#89b4fa"],
                            hole=0.4,
                        )
                        fig_sent.update_layout(
                            plot_bgcolor="#1e1e2e",
                            paper_bgcolor="#1e1e2e",
                            font_color="#cdd6f4",
                            showlegend=True,
                            height=250,
                            margin=dict(t=20, b=0),
                        )
                        st.plotly_chart(fig_sent, use_container_width=True)
                    st.markdown("**Recent Headlines**")
                    for h in headlines[:5]:
                        st.markdown(f"- {h}")
                else:
                    st.info("No recent news found")
        except Exception as e:
            st.error(f"Sentiment analysis unavailable: {e}")
else:
    st.info("Enter a symbol and click Analyze to load market data.")
