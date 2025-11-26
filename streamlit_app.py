import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import time

# Page config
st.set_page_config(page_title="Amit's Pro OI Dashboard", layout="wide", page_icon="📊")

# Pro UI CSS
st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #0a0e17 0%, #1a1c23 100%); color: white; }
    h1 { color: #00ff41; text-align: center; font-size: 3rem; text-shadow: 0 0 20px #00ff41; }
    .metric { color: white; }
    .stMetric { background: #111; border-radius: 10px; padding: 10px; }
    .live-tag { background: #ff0066; color: white; padding: 5px 10px; border-radius: 20px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

st.markdown("<h1>🟢 AMIT'S PRO OI TERMINAL</h1>", unsafe_allow_html=True)

# Sidebar - Index & Expiry Selector
st.sidebar.title("⚙️ Controls")
index = st.sidebar.selectbox("Index", ["NIFTY", "BANKNIFTY", "FINNIFTY"])
refresh_sec = st.sidebar.slider("Refresh (sec)", 5, 30, 7)

# Live Tag
st.sidebar.markdown('<div class="live-tag">LIVE</div>', unsafe_allow_html=True)

# Session for NSE
@st.cache_resource(ttl=3600)
def get_session():
    s = requests.Session()
    s.headers.update({"User-Agent": "Mozilla/5.0", "Referer": "https://www.nseindia.com/option-chain"})
    return s

session = get_session()

# Fetch Data Function (TOI & COI Separate)
def fetch_data(index):
    try:
        url = f"https://www.nseindia.com/api/option-chain-indices?symbol={index}"
        json_data = session.get(url, timeout=15).json()
        records = json_data["records"]["data"]
        price = json_data["records"]["underlyingValue"]
        atm = int(round(price / 50)) * 50
        lot = {"BANKNIFTY": 15, "FINNIFTY": 25}.get(index, 25)

        toi_ce = toi_pe = coi_ce = coi_pe = atm_ce = atm_pe = 0
        for item in records:
            sp = item["strikePrice"]
            if atm - 400 <= sp <= atm + 400:  # Near ATM
                if "CE" in item:
                    toi_ce += item["CE"]["openInterest"]
                    coi_ce += item["CE"]["changeinOpenInterest"]
                    if sp == atm: atm_ce = item["CE"]["lastPrice"]
                if "PE" in item:
                    toi_pe += item["PE"]["openInterest"]
                    coi_pe += item["PE"]["changeinOpenInterest"]
                    if sp == atm: atm_pe = item["PE"]["lastPrice"]

        toi_ce_l = round(toi_ce * lot / 100000, 1)
        toi_pe_l = round(toi_pe * lot / 100000, 1)
        coi_ce_l = round(coi_ce * lot / 100000, 1)
        coi_pe_l = round(coi_pe * lot / 100000, 1)
        straddle = round(atm_ce + atm_pe, 1)
        pcr = round(toi_pe / toi_ce, 2) if toi_ce > 0 else 0

        return {
            "price": round(price, 2),
            "atm": atm,
            "toi_ce": toi_ce_l,
            "toi_pe": toi_pe_l,
            "coi_ce": coi_ce_l,
            "coi_pe": coi_pe_l,
            "straddle": straddle,
            "pcr": pcr,
            "time": datetime.now().strftime("%H:%M:%S")
        }
    except:
        return None

# History - FIXED: Initialize with all columns to avoid concat error
if "history" not in st.session_state:
    st.session_state.history = pd.DataFrame(columns=["price", "atm", "toi_ce", "toi_pe", "coi_ce", "coi_pe", "straddle", "pcr", "time"])

ph = st.empty()
while True:
    with ph.container():
        data = fetch_data(index)
        if not data:
            st.error("Market Closed or Loading...")
            time.sleep(refresh_sec)
            continue

        # Update History - FIXED: Ensure new_row has all columns
        new_row = pd.DataFrame([data])
        st.session_state.history = pd.concat([st.session_state.history, new_row], ignore_index=True)
        if len(st.session_state.history) > 100:
            st.session_state.history = st.session_state.history.tail(100)
        df = st.session_state.history

        # Header with Index
        col_h1, col_h2 = st.columns([2, 1])
        with col_h1:
            st.markdown(f"**{index} | ATM: {data['atm']} | Price: ₹{data['price']:,}**")
        with col_h2:
            st.metric("PCR", data["pcr"])

        # TOI & COI Separate Metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("**CE TOI**", f"{data['toi_ce']}L")
        with col2:
            st.metric("**PE TOI**", f"{data['toi_pe']}L")
        with col3:
            st.metric("**CE COI**", f"{data['coi_ce']:+.1f}L")
        with col4:
            st.metric("**PE COI**", f"{data['coi_pe']:+.1f}L")

        # Pro Charts - TradingTick Style (Bar for COI + Line for Price)
        col_c1, col_c2 = st.columns([2, 1])
        with col_c1:
            st.subheader("📈 Live OI Change (TradingTick Style)")
            fig = go.Figure()
            fig.add_trace(go.Bar(x=df["time"], y=df["coi_ce"], name="CE COI", marker_color="#00ff41"))
            fig.add_trace(go.Bar(x=df["time"], y=df["coi_pe"], name="PE COI", marker_color="#ff0066"))
            fig.add_trace(go.Scatter(x=df["time"], y=df["price"], name="Price", yaxis="y2", line=dict(color="yellow", width=2)))
            fig.update_layout(template="plotly_dark", height=400, barmode="group", xaxis_title="Time", yaxis_title="COI (Lakhs)")
            fig.update_yaxes(title_text="Price", secondary_y=True, side="right")
            st.plotly_chart(fig, use_container_width=True)

        with col_c2:
            st.subheader("💰 ATM Straddle")
            st.metric("Straddle Premium", f"₹{data['straddle']}")

        # Footer
        st.markdown("**NSE Official Data | Made by Amit Bhai | Pro Traders Only**")

    time.sleep(refresh_sec)
