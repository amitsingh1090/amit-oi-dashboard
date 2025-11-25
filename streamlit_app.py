# streamlit_app.py (MODULAR VERSION)
import streamlit as st
from data.nse_fetcher import get_live_data
from components.summary import show as show_summary
from components.charts import show_chart
import time

st.set_page_config(page_title="Amit Pro Terminal", layout="wide")
st.title("AMIT'S MODULAR OI DASHBOARD")

if "history" not in st.session_state:
    st.session_state.history = []

ph = st.empty()
while True:
    with ph.container():
        data = get_live_data()
        if not data:
            st.error("Loading...")
            time.sleep(7)
            continue

        st.session_state.history.append(data)
        if len(st.session_state.history) > 100:
            st.session_state.history = st.session_state.history[-100:]

        df = pd.DataFrame(st.session_state.history)

        col1, col2 = st.columns([1, 2])
        with col1:
            show_summary(data)
        with col2:
            show_chart(df)

        st.caption(f"NSE Official • {data['time']} • Made by Amit")
    time.sleep(7)
