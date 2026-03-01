import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
from services.portfolio import (
    get_account,
    get_positions,
    get_open_orders,
    submit_order,
    cancel_order,
    close_all_positions,
    is_connected,
)
from services.market_data import get_quote
from services.risk import calculate_position_size
from services.sentiment import estimate_sentiment
from services.market_data import get_news_headlines

st.set_page_config(page_title="Live Trading | QuantEdge", layout="wide")

st.title("Live Trading")
st.markdown("Execute trades and manage automated strategy execution via Alpaca")

connected = is_connected()
if connected:
    st.success("Connected to Alpaca broker")
else:
    st.error("Not connected to Alpaca. Configure credentials in Settings.")

tab1, tab2, tab3 = st.tabs(["Manual Orders", "Automated Strategy", "Order Management"])

with tab1:
    st.subheader("Place Order")
    if not connected:
        st.info("Connect to Alpaca to place orders")
    else:
        with st.form("order_form"):
            col1, col2 = st.columns(2)
            with col1:
                order_symbol = st.text_input("Symbol", value="SPY").upper()
                order_side = st.selectbox("Side", ["buy", "sell"])
                order_qty = st.number_input("Quantity", min_value=1, value=1)
            with col2:
                order_type = st.selectbox("Order Type", ["market", "limit", "stop"])
                limit_price = st.number_input("Limit Price ($)", min_value=0.0, value=0.0)
                stop_loss = st.number_input("Stop Loss ($)", min_value=0.0, value=0.0)
                take_profit = st.number_input("Take Profit ($)", min_value=0.0, value=0.0)

            preview_btn = st.form_submit_button("Preview Order")

        if preview_btn:
            try:
                quote = get_quote(order_symbol)
                current_price = quote.get("price", 0)
                estimated_value = order_qty * current_price
                st.info(f"Current price: ${current_price:.2f} | Estimated value: ${estimated_value:,.2f}")

                with st.form("confirm_order_form"):
                    st.warning(f"Confirm: {order_side.upper()} {order_qty} shares of {order_symbol}")
                    confirm_btn = st.form_submit_button("Confirm and Submit", type="primary")

                if confirm_btn:
                    try:
                        result = submit_order(
                            symbol=order_symbol,
                            qty=order_qty,
                            side=order_side,
                            order_type=order_type,
                            limit_price=limit_price if limit_price > 0 else None,
                            take_profit_price=take_profit if take_profit > 0 else None,
                            stop_loss_price=stop_loss if stop_loss > 0 else None,
                        )
                        st.success(f"Order submitted: {result}")
                    except Exception as e:
                        st.error(f"Order failed: {e}")
            except Exception as e:
                st.error(f"Failed to fetch quote: {e}")

with tab2:
    st.subheader("Automated Strategy Runner")
    st.markdown("Run a sentiment-driven strategy that analyzes news and places trades automatically")

    col_a, col_b = st.columns(2)
    with col_a:
        auto_symbol = st.text_input("Symbol", value="SPY", key="auto_sym").upper()
        auto_threshold = st.slider("Sentiment Threshold", 0.5, 0.99, 0.75)
        auto_cash_risk = st.slider("Cash at Risk", 0.05, 0.5, 0.1)
    with col_b:
        use_stop_loss = st.checkbox("Enable Stop Loss", value=True)
        stop_loss_pct = st.slider("Stop Loss %", 1.0, 10.0, 5.0) / 100
        use_take_profit = st.checkbox("Enable Take Profit", value=True)
        take_profit_pct = st.slider("Take Profit %", 5.0, 30.0, 15.0) / 100

    if st.button("Run Single Iteration", disabled=not connected):
        with st.spinner("Analyzing sentiment and market conditions..."):
            try:
                headlines = get_news_headlines(auto_symbol)
                if not headlines:
                    st.warning("No recent news found for analysis")
                else:
                    probability, sentiment = estimate_sentiment(headlines[:10])
                    st.markdown(f"**Sentiment:** {sentiment.upper()} ({probability:.1%} confidence)")
                    st.markdown(f"**Headlines analyzed:** {len(headlines[:10])}")

                    if probability > auto_threshold and sentiment != "neutral":
                        account = get_account()
                        if account:
                            cash = float(account.get("cash", 0))
                            quote = get_quote(auto_symbol)
                            price = quote.get("price", 0)

                            qty = calculate_position_size(cash, price, auto_cash_risk, stop_loss_pct)
                            if qty > 0:
                                side = "buy" if sentiment == "positive" else "sell"
                                tp = price * (1 + take_profit_pct) if sentiment == "positive" else price * (1 - take_profit_pct)
                                sl = price * (1 - stop_loss_pct) if sentiment == "positive" else price * (1 + stop_loss_pct)

                                result = submit_order(
                                    symbol=auto_symbol,
                                    qty=qty,
                                    side=side,
                                    order_type="market",
                                    take_profit_price=tp if use_take_profit else None,
                                    stop_loss_price=sl if use_stop_loss else None,
                                )
                                st.success(f"Order placed: {side.upper()} {qty} shares of {auto_symbol} at ~${price:.2f}")
                            else:
                                st.info("Position size too small based on risk parameters")
                        else:
                            st.error("Could not fetch account data")
                    else:
                        st.info(f"Sentiment threshold not met ({probability:.1%} < {auto_threshold:.1%}). No trade placed.")
            except Exception as e:
                st.error(f"Strategy execution failed: {e}")

with tab3:
    st.subheader("Open Orders")
    if connected:
        orders = get_open_orders()
        if orders:
            df_orders = pd.DataFrame(orders)
            st.dataframe(df_orders, use_container_width=True, hide_index=True)

            cancel_id = st.text_input("Order ID to cancel")
            if st.button("Cancel Order", disabled=not cancel_id):
                if cancel_order(cancel_id):
                    st.success(f"Order {cancel_id} cancelled")
                    st.rerun()
                else:
                    st.error("Failed to cancel order")

            if st.button("Close All Positions", type="primary"):
                if close_all_positions():
                    st.success("All positions closed")
                else:
                    st.error("Failed to close positions")
        else:
            st.info("No open orders")
    else:
        st.info("Connect to Alpaca to manage orders")
