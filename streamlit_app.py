import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import time

st.set_page_config(page_title="Amit Pro OI Terminal", layout="wide", page_icon="Chart increasing")

# TradingTick Exact Theme
st.markdown("""
<style>
    .stApp { background: #f8f9fa; font-family: 'Segoe UI', sans-serif; }
    .header { background: #0d6efd; color: white; padding: 15px; border-radius: 10px; text-align: center; font-size: 2rem; font-weight: bold; }
    .metric-card { background: white; border: 1px solid #dee2e6; border-radius: 10px; padding: 15px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
    .stMetric { background: white !important; }
    .stMetric label { color: #0d6efd !important; font-weight: bold; }
    .live { color: #dc3545; font-weight: bold; animation: blink 1.5s infinite; }
    @keyframes blink { 0%,100% { opacity: 0.5; } 50% { opacity: 1; } }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<div class="header">AMIT\'S PRO OI TERMINAL</div>', unsafe_allow_html=True)

col1, col2, col3 = st.columns([1, 2, 1])
with col1:
    index = st.selectbox("Index", ["NIFTY", "BANKNIFTY", "FINNIFTY"])
with col2:
    expiry = st.selectbox("Expiry", ["Weekly", "Monthly", "Next Week"])
with col3:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="live">● LIVE</div>', unsafe_allow_html=True)

refresh = st.slider("Refresh (sec)", 5, 30, 10, key="refresh")

# Session
@st.cache_resource(ttl=3600)
def get_session():
    s = requests.Session()
    s.headers.update({
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://www.nseindia.com/option-chain"
    })
    s.get("https://www.nseindia.com")
    return s

session = get_session()

def get_data():
    try:
        url = f"https://www.nseindia.com/api/option-chain-indices?symbol={index}"
        data = session.get(url, timeout=10).json()["records"]
        
        price = data["underlyingValue"]
        timestamp = data["timestamp"]
        nse_time = datetime.strptime(timestamp, "%d-%b-%Y %H:%M:%S").strftime("%H:%M")
        
        ce_oi = pe_oi = ce_ch = pe_ch = 0
        for item in data["data"]:
            if "CE" in item:
                ce_oi += item["CE"]["openInterest"]
                ce_ch += item["CE"]["changeinOpenInterest"]
            if "PE" in item:
                pe_oi += item["PE"]["openInterest"]
                pe_ch += item["PE"]["changeinOpenInterest"]
        
        lot = 25 if index == "NIFTY" else 15
        pcr = round(pe_oi / ce_oi, 2) if ce_oi > 0 else 0
        
        return {
            "price": round(price, 2),
            "ce_oi": round(ce_oi * lot / 100000, 1),
            "pe_oi": round(pe_oi * lot / 100000, 1),
            "ce_ch": round(ce_ch * lot / 100000, 1),
            "pe_ch": round(pe_ch * lot / 100000, 1),
            "pcr": pcr,
            "time": nse_time
        }
    except:
        return None

if "df" not in st.session_state:
    st.session_state.df = pd.DataFrame()

ph = st.empty()
while True:
    with ph.container():
        data = get_data()
        if not data:
            st.warning("Waiting for NSE data...")
            time.sleep(refresh)
            continue
            
        # Save history
        new_row = pd.DataFrame([{
            "time": data["time"],
            "ce_ch": data["ce_ch"],
            "pe_ch": data["pe_ch"],
            "price": data["price"]
        }])
        st.session_state.df = pd.concat([st.session_state.df, new_row], ignore_index=True)
        st.session_state.df = st.session_state.df.tail(100)
        df = st.session_state.df

        # Metrics
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            st.metric("CE OI", f"{data['ce_oi']}L")
        with c2:
            st.metric("PE OI", f"{data['pe_oi']}L")
        with c3:
            st.metric("CE Change", f"{data['ce_ch']:+.1f}L")
        with c4:
            st.metric("PE Change", f"{data['pe_ch']:+.1f}L")
        with c5:
            st.metric("PCR", data["pcr"])

        # TradingTick Exact Chart
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df["time"], y=df["ce_ch"], name="CE", mode="lines+markers", line=dict(color="#28a745", width=3)))
        fig.add_trace(go.Scatter(x=df["time"], y=df["pe_ch"], name="PE", mode="lines+markers", line=dict(color="#dc3545", width=3)))
        fig.add_trace(go.Scatter(x=df["time"], y=df["price"], name="Future Price", yaxis="y2", line=dict(color="#ffc107", width=3)))

        fig.update_layout(
            height=500,
            plot_bgcolor="white",
            paper_bgcolor="white",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            xaxis=dict(title="Time", tickangle=45),
            yaxis=dict(title="Change in OI (Lakhs)", side="left"),
            yaxis2=dict(title="Future Price", overlaying="y", side="right")
        )
        st.plotly_chart(fig, use_container_width=True)

        st.caption(f"As of {data['time']} • Expiry: {expiry} • NSE Official Data • Made by Amit Bhai")

    time.sleep(refresh)
