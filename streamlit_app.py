import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import time

st.set_page_config(page_title="Amit's Pro OI Terminal", layout="wide", page_icon="Chart increasing")

# Pro Dark Theme + Proper Visibility
st.markdown("""
<style>
    .stApp { background: #0e1117; color: white; }
    h1 { color: #00ff41; text-align: center; font-size: 3rem; text-shadow: 0 0 15px #00ff41; }
    .stMetric { background: rgba(30,35,45,0.9); border: 1px solid #333; border-radius: 12px; padding: 15px; }
    .stMetric > div > div { color: white !important; font-size: 1.4rem !important; }
    .stMetric label { color: #00ff41 !important; font-weight: bold; }
    .live-tag { background: #ff0066; padding: 8px 15px; border-radius: 30px; font-weight: bold; animation: pulse 2s infinite; }
    @keyframes pulse { 0% { box-shadow: 0 0 0 0 rgba(255,0,102,0.7); } 70% { box-shadow: 0 0 0 10px rgba(255,0,102,0); } 100% { box-shadow: 0 0 0 0 rgba(255,0,102,0); } }
</style>
""", unsafe_allow_html=True)

st.markdown("<h1>AMIT'S PRO OI TERMINAL</h1>", unsafe_allow_html=True)

# Sidebar
st.sidebar.title("Controls")
index = st.sidebar.selectbox("Index", ["NIFTY", "BANKNIFTY", "FINNIFTY"])
refresh_sec = st.sidebar.slider("Refresh (sec)", 5, 20, 7)
st.sidebar.markdown('<div class="live-tag">● LIVE</div>', unsafe_allow_html=True)

# NSE Session
@st.cache_resource(ttl=3600)
def get_session():
    s = requests.Session()
    s.headers.update({"User-Agent": "Mozilla/5.0", "Referer": "https://www.nseindia.com"})
    return s
session = get_session()

# Fetch Data
def fetch_data():
    try:
        url = f"https://www.nseindia.com/api/option-chain-indices?symbol={index}"
        data = session.get(url, timeout=10).json()
        records = data["records"]["data"]
        price = data["records"]["underlyingValue"]
        atm = int(round(price / 50) * 50)
        lot = 25 if index == "NIFTY" else 15 if index == "BANKNIFTY" else 25

        toi_ce = toi_pe = coi_ce = coi_pe = atm_ce = atm_pe = 0
        for r in records:
            sp = r["strikePrice"]
            if atm - 500 <= sp <= atm + 500:
                if "CE" in r:
                    toi_ce += r["CE"]["openInterest"]
                    coi_ce += r["CE"]["changeinOpenInterest"]
                    if sp == atm: atm_ce = r["CE"]["lastPrice"]
                if "PE" in r:
                    toi_pe += r["PE"]["openInterest"]
                    coi_pe += r["PE"]["changeinOpenInterest"]
                    if sp == atm: atm_pe = r["PE"]["lastPrice"]

        return {
            "price": round(price, 2),
            "atm": atm,
            "toi_ce": round(toi_ce * lot / 100000, 1),
            "toi_pe": round(toi_pe * lot / 100000, 1),
            "coi_ce": round(coi_ce * lot / 100000, 1),
            "coi_pe": round(coi_pe * lot / 100000, 1),
            "straddle": round(atm_ce + atm_pe),
            "pcr": round(toi_pe / toi_ce, 2) if toi_ce else 0,
            "time": datetime.now().strftime("%H:%M:%S")
        }
    except:
        return None

# History - Fixed
if "history" not in st.session_state:
    st網站.session_state.history = pd.DataFrame(columns=["price","toi_ce","toi_pe","coi_ce","coi_pe","straddle","pcr","time"])

ph = st.empty()
while True:
    with ph.container():
        data = fetch_data()
        if not data:
            st.error("Market Closed • Kal 9:15 se live hoga")
            time.sleep(refresh_sec)
            continue

        # Append data
        new_row = pd.DataFrame([data])
        st.session_state.history = pd.concat([st.session_state.history, new_row], ignore_index=True)
        st.session_state.history = st.session_state.history.tail(100)
        df = st.session_state.history

        # Header
        st.markdown(f"**{index} • ATM {data['atm']} • Price ₹{data['price']:,}**")

        # Metrics - Now Fully Visible
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("CE TOI", f"{data['toi_ce']}L")
        c2.metric("PE TOI", f"{data['toi_pe']}L")
        c3.metric("CE COI", f"{data['coi_ce']:+.1f}L", delta_color="normal")
        c4.metric("PE COI", f"{data['coi_pe']:+.1f}L", delta_color="normal")

        # Chart - Fixed Secondary Axis Error + Proper Colors
        col1, col2 = st.columns([3,1])
        with col1:
            st.subheader("Live OI Change (TradingTick Style)")
            fig = go.Figure()
            fig.add_trace(go.Bar(x=df["time"], y=df["coi_ce"], name="CE COI", marker_color="#00ff41"))
            fig.add_trace(go.Bar(x=df["time"], y=df["coi_pe"], name="PE COI", marker_color="#ff0066"))
            fig.add_trace(go.Scatter(x=df["time"], y=df["price"], name="Price", yaxis="y2", 
                                   line=dict(color="#fff200", width=3)))

            fig.update_layout(
                template="plotly_dark",
                height=450,
                barmode="relative",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                yaxis=dict(title="COI (Lakhs)"),
                yaxis2=dict(title="Price", overlaying="y", side="right", showgrid=False)
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.metric("ATM Straddle", f"₹{data['straddle']}")
            st.metric("PCR", data['pcr'])

        st.caption(f"Updated: {data['time']} • Made by Amit Bhai")

    time.sleep(refresh_sec)
