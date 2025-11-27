import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import time

st.set_page_config(page_title="Amit Pro OI Terminal - TradingTick Style", layout="wide", page_icon="Chart increasing")

# TradingTick Exact UI Theme
st.markdown("""
<style>
    .stApp { background: #f8f9fa; }
    .header { background: #0d6efd; color: white; padding: 20px; border-radius: 12px; text-align: center; font-size: 2.2rem; font-weight: bold; margin-bottom: 20px; }
    .metric-box { background: white; padding: 18px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); border: 1px solid #e0e0e0; }
    .stMetric label { color: #0d6efd !important; font-weight: bold; font-size: 1rem !important; }
    .stMetric > div > div { font-size: 1.8rem !important; font-weight: bold; color: #212529 !important; }
    .live-dot { color: #dc3545; font-size: 2rem; animation: pulse 2s infinite; }
    @keyframes pulse { 0% { opacity: 0.6; } 50% { opacity: 1; } 100% { opacity: 0.6; } }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<div class="header">AMIT\'S PRO OI TERMINAL</div>', unsafe_allow_html=True)

# Controls
col1, col2, col3 = st.columns([2, 2, 1])
with col1:
    index = st.selectbox("Index", ["NIFTY", "BANKNIFTY", "FINNIFTY"])
with col2:
    expiry = st.selectbox("Expiry", ["Current Week", "Next Week", "Monthly"])
with col3:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="live-dot">● LIVE</div>', unsafe_allow_html=True)

refresh_sec = st.slider("Refresh (seconds)", 5, 20, 8, key="refresh")

# NSE Session
@st.cache_resource(ttl=3600)
def get_session():
    s = requests.Session()
    s.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Referer": "https://www.nseindia.com/option-chain",
        "Accept": "application/json"
    })
    s.get("https://www.nseindia.com")
    return s

session = get_session()

def fetch_data():
    try:
        url = f"https://www.nseindia.com/api/option-chain-indices?symbol={index}"
        resp = session.get(url, timeout=10).json()["records"]
        
        price = resp["underlyingValue"]
        timestamp = resp["timestamp"]
        nse_time = datetime.strptime(timestamp, "%d-%b-%Y %H:%M:%S").strftime("%H:%M")
        
        total_ce_oi = total_pe_oi = total_ce_change = total_pe_change = 0
        for item in resp["data"]:
            if "CE" in item:
                total_ce_oi += item["CE"]["openInterest"]
                total_ce_change += item["CE"]["changeinOpenInterest"]
            if "PE" in item:
                total_pe_oi += item["PE"]["openInterest"]
                total_pe_change += item["PE"]["changeinOpenInterest"]
        
        lot = 25 if index == "NIFTY" else 15 if index == "BANKNIFTY" else 25
        pcr = round(total_pe_oi / total_ce_oi, 2) if total_ce_oi > 0 else 0
        
        return {
            "price": round(price, 2),
            "ce_oi": round(total_ce_oi * lot / 100000, 1),
            "pe_oi": round(total_pe_oi * lot / 100000, 1),
            "ce_change": round(total_ce_change * lot / 100000, 1),
            "pe_change": round(total_pe_change * lot / 100000, 1),
            "pcr": pcr,
            "time": nse_time
        }
    except:
        return None

# Initialize history
if "history" not in st.session_state:
    st.session_state.history = pd.DataFrame(columns=["time", "ce_change", "pe_change", "price"])

ph = st.empty()

while True:
    with ph.container():
        data = fetch_data()
        if not data:
            st.info("Waiting for market data...")
            time.sleep(refresh_sec)
            continue

        # Append to history
        new_row = pd.DataFrame([{
            "time": data["time"],
            "ce_change": data["ce_change"],
            "pe_change": data["pe_change"],
            "price": data["price"]
        }])
        st.session_state.history = pd.concat([st.session_state.history, new_row], ignore_index=True)
        st.session_state.history = st.session_state.history.tail(120)  # Last 2 hours approx
        df = st.session_state.history

        # Header Info
        st.markdown(f"### {index} • ₹{data['price']:,} • NSE Time: {data['time']} • Expiry: {expiry}")

        # Metrics Row
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            st.metric("**CE OI**", f"{data['ce_oi']}L")
        with c2:
            st.metric("**PE OI**", f"{data['pe_oi']}L")
        with c3:
            st.metric("**CE Change**", f"{data['ce_change']:+.1f}L")
        with c4:
            st.metric("**PE Change**", f"{data['pe_change']:+.1f}L")
        with c5:
            st.metric("**PCR**", data["pcr"])

        # TRADINGTICK EXACT DUAL-AXIS LINE CHART
        fig = go.Figure()

        # CE Change (Green Line)
        fig.add_trace(go.Scatter(
            x=df["time"], y=df["ce_change"],
            mode='lines+markers',
            name='CE Change',
            line=dict(color='#28a745', width=3),
            marker=dict(size=6)
        ))

        # PE Change (Red Line)
        fig.add_trace(go.Scatter(
            x=df["time"], y=df["pe_change"],
            mode='lines+markers',
            name='PE Change',
            line=dict(color='#dc3545', width=3),
            marker=dict(size=6)
        ))

        # Future Price (Yellow Line - Right Axis)
        fig.add_trace(go.Scatter(
            x=df["time"], y=df["price"],
            mode='lines',
            name='Future Price',
            yaxis="y2",
            line=dict(color='#ffc107', width=4)
        ))

        fig.update_layout(
            height=550,
            plot_bgcolor="white",
            paper_bgcolor="white",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            xaxis=dict(title="Time", tickangle=45, gridcolor="#e0e0e0"),
            yaxis=dict(title="Change in OI (Lakhs)", gridcolor="#e0e0e0", side="left"),
            yaxis2=dict(title="Future Price", overlaying="y", side="right", showgrid=False),
            hovermode="x unified",
            margin=dict(l=50, r=50, t=50, b=50)
        )

        st.plotly_chart(fig, use_container_width=True)

        st.caption(f"• Last Updated: {data['time']} • 100% NSE Official • Made with ❤️ by Amit Bhai")

    time.sleep(refresh_sec)
