import streamlit as st
from components.summary_cards import show_summary
from components.oi_change_chart import show_oi_change_chart
from components.straddle_chart import show_straddle_chart
from components.net_signal import show_net_signal
from data.nse_fetcher import get_latest_data
import time

st.set_page_config(page_title="Amit Pro OI Terminal", layout="wide", page_icon="Fire")
st.title("AMIT'S ULTIMATE MODULAR OI DASHBOARD")

placeholder = st.empty()

while True:
    with placeholder.container():
        data, df = get_latest_data()
        if not data:
            st.error("Market Closed • Retrying...")
            time.sleep(8)
            continue

        col1, col2 = st.columns([1.3, 2.7])
        with col1:
            show_summary(data)
            show_net_signal(data)
        with col2:
            show_oi_change_chart(df)
            show_straddle_chart(df)

        st.caption(f"Data: NSE Official • Updated: {data['time']} • Made by Amit")
    time.sleep(7)
