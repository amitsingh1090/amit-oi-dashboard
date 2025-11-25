# streamlit_app.py → FINAL WORKING VERSION
import streamlit as st
import pandas as pd
import time
from data.nse_fetcher import get_live_data
from components.summary import show as show_summary
from components.charts import show_chart

st.set_page_config(page_title="Amit Pro OI Terminal", layout="wide", page_icon="Chart increasing")
st.markdown("<h1 style='text-align: center; color: #00ff41;'>AMIT'S MODULAR OI DASHBOARD</h1>", unsafe_allow_html=True)

if "history" not in st.session_state:
    st.session_state.history = []

placeholder = st.empty()

while True:
    with placeholder.container():
        data = get_live_data()
        
        if data is None:
            st.warning("Market Closed • Data kal 9:15 AM se live hoga")
            time.sleep(10)
            continue

        # Add to history
        st.session_state.history.append(data)
        if len(st.session_state.history) > 150:
            st.session_state.history = st.session_state.history[-150:]

        df = pd.DataFrame(st.session_state.history)

        col1, col2 = st.columns([1, 3])

        with col1:
            show_summary(data)
            st.markdown(f"**Updated:** {data['time']}")

        with col2:
            show_chart(df)

        st.success(f"NSE Official Live • {data['time']} • Made by Amit Bhai")

    time.sleep(7)
