# streamlit_app.py (FINAL 100% WORKING MODULAR VERSION)
import streamlit as st
import pandas as pd
import time
from data.nse_fetcher import get_live_data
from components.summary import show as show_summary
from components.charts import show_chart

st.set_page_config(page_title="Amit Pro Terminal", layout="wide", page_icon="Chart")
st.title("AMIT'S MODULAR OI DASHBOARD")

# Initialize history properly
if "history" not in st.session_state:
    st.session_state.history = []

placeholder = st.empty()

while True:
    with placeholder.container():
        data = get_live_data()
        if not data:
            st.warning("Market Closed • Waiting for data...")
            time.sleep(8)
            continue

        # Add new data to history
        st.session_state.history.append(data)
        if len(st.session_state.history) > 100:
            st.session_state.history = st.session_state.history[-100:]

        # Convert to DataFrame only when needed
        df = pd.DataFrame(st.session_state.history)

        col1, col2 = st.columns([1, 2.2])
        
        with col1:
            show_summary(data)
            st.caption(f"Updated: {data['time']}")

        with col2:
            show_chart(df)

        st.success(f"NSE Official Live Data • {data['time']} • Made by Amit Bhai")

    time.sleep(7)
