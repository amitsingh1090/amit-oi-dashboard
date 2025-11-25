# components/summary.py
import streamlit as st

def show(data):
    c1, c2 = st.columns(2)
    with c1:
        st.metric("CE OI", f"{data['ce_oi']}L", f"{data['ce_chg']:+}")
        st.metric("PE OI", f"{data['pe_oi']}L", f"{data['pe_chg']:+}")
    with c2:
        st.metric("Straddle", f"₹{data['straddle']}")
        st.metric("Price", f"₹{data['price']:,}")
