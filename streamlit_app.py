import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import time
import os

st.set_page_config(page_title="Amit Pro OI Terminal", layout="wide", page_icon="Chart increasing")

# Light Clean Theme + Logo Header
st.markdown("""
<style>
    .stApp { background: #f8f9fa; }
    .header-bar {
        background: linear-gradient(90deg, #007bff, #00d4ff);
        padding: 12px 20px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 1.8rem;
        font-weight: bold;
        box-shadow: 0 4px 15px rgba(0,123,255,0.3);
        margin-bottom: 20px;
    }
    .logo { height: 50px; margin-right: 15px; border-radius: 10px; }
    .stMetric label { color: #007bff !important; font-weight: bold; }
    .stMetric > div > div { font-size: 1.8rem !important; font-weight: bold; }
    .live { color: #dc3545; font-size: 2rem; animation: pulse 1.8s infinite; }
    @keyframes pulse { 0%,100% { opacity: 0.7; } 50% { opacity: 1; } }
</style>
""", unsafe_allow_html=True)

# Header with Logo
st.markdown("""
<div class="header-bar">
    <img src="https://i.imgur.com/7Y5X2hX.png" class="logo">
    AMIT'S PRO OI TERMINAL
</div>
""", unsafe_allow_html=True)

# Controls
col1, col2, col3 = st.columns([2,2,1])
with col1:
    index = st.selectbox("Index", ["NIFTY", "BANKNIFTY", "FINNIFTY"])
with col2:
    expiry_type = st.selectbox("Expiry", ["Current Week", "Next Week", "Monthly"])
with col3:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="live">LIVE</div>', unsafe_allow_html=True)

refresh = st.slider("Refresh (sec)", 5, 20, 7)

# Session
@st.cache_resource(ttl=3600)
def get_session():
    s = requests.Session()
    s.headers.update({"User-Agent": "Mozilla/5.0", "Referer": "https://www.nseindia.com"})
    s.get("https://www.nseindia.com")
    return s
session = get_session()

# Load/Save History
HISTORY_FILE = "oi_history.csv"
if os.path.exists(HISTORY_FILE):
    history_df = pd.read_csv(HISTORY_FILE)
else:
    history_df = pd.DataFrame(columns=["timestamp", "index", "expiry", "price", "ce_oi", "pe_oi", "ce_change", "pe_change", "pcr"])

def fetch_filtered_oi():
    try:
        url = f"https://www.nseindia.com/api/option-chain-indices?symbol={index}"
        data = session.get(url, timeout=12).json()["records"]
        
        price = data["underlyingValue"]
        timestamp = data["timestamp"]
        nse_time = datetime.strptime(timestamp, "%d-%b-%Y %H:%M:%S")
        time_str = nse_time.strftime("%H:%M")
        date_str = nse_time.strftime("%d-%b-%Y")

        # Get expiry dates
        expiries = [e["expiryDate"] for e in data["expiryDates"]]
        target_expiry = expiries[0] if expiry_type == "Current Week" else expiries[1] if len(expiries)>1 else expiries[0]
        if expiry_type == "Monthly": target_expiry = expiries[-1]

        ce_oi = pe_oi = ce_ch = pe_ch = 0
        for item in data["data"]:
            if item.get("expiryDate") == target_expiry:
                if "CE" in item:
                    ce_oi += item["CE"]["openInterest"]
                    ce_ch += item["CE"]["changeinOpenInterest"]
                if "PE" in item:
                    pe_oi += item["PE"]["openInterest"]
                    pe_ch += item["PE"]["changeinOpenInterest"]

        lot = 25 if index == "NIFTY" else 15 if index == "BANKNIFTY" else 25
        pcr = round(pe_oi / ce_oi, 2) if ce_oi > 0 else 0

        result = {
            "timestamp": nse_time,
            "time": time_str,
            "price": round(price, 2),
            "ce_oi": round(ce_oi * lot / 100000, 1),
            "pe_oi": round(pe_oi * lot / 100000, 1),
            "ce_change": round(ce_ch * lot / 100000, 1),
            "pe_change": round(pe_ch * lot / 100000, 1),
            "pcr": pcr,
            "expiry": expiry_type
        }

        # Save to history
        new_row = pd.DataFrame([{**result, "index": index}])
        global history_df
        history_df = pd.concat([history_df, new_row], ignore_index=True)
        history_df.to_csv(HISTORY_FILE, index=False)

        return result
    except:
        return None

# Main Loop
ph = st.empty()
while True:
    with ph.container():
        data = fetch_filtered_oi()
        if not data:
            st.warning("Market Closed or Loading...")
            time.sleep(refresh)
            continue

        # Filter history for current index + expiry
        mask = (history_df["index"] == index) & (history_df["expiry"] == expiry_type)
        chart_df = history_df[mask].tail(80).copy()
        chart_df["time"] = pd.to_datetime(chart_df["timestamp"]).dt.strftime("%H:%M")

        # Header Info
        st.markdown(f"### {index} • ₹{data['price']:,} • Time: {data['time']} • Expiry: {expiry_type}")

        # Metrics
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("CE OI", f"{data['ce_oi']}L")
        c2.metric("PE OI", f"{data['pe_oi']}L")
        c3.metric("CE Change", f"{data['ce_change']:+.1f}L")
        c4.metric("PE Change", f"{data['pe_change']:+.1f}L")
        c5.metric("PCR", data["pcr"])

        # BAR CHART WITH VALUES ON BARS (TradingTick Style)
        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=chart_df["time"], y=chart_df["ce_oi"],
            name="CE OI", marker_color="#28a745",
            text=chart_df["ce_oi"], textposition="outside"
        ))
        fig.add_trace(go.Bar(
            x=chart_df["time"], y=chart_df["pe_oi"]*-1,
            name="PE OI", marker_color="#dc3545",
            text=chart_df["pe_oi"].abs(), textposition="outside"
        ))
        fig.add_trace(go.Scatter(
            x=chart_df["time"], y=chart_df["price"],
            name="Future Price", yaxis="y2",
            line=dict(color="#ffc107", width=4)
        ))

        fig.update_layout(
            height=550,
            barmode="relative",
            plot_bgcolor="white",
            paper_bgcolor="white",
            legend=dict(orientation="h", y=1.02, x=1),
            yaxis=dict(title="Open Interest (Lakhs)"),
            yaxis2=dict(title="Price", overlaying="y", side="right", showgrid=False),
            xaxis_tickangle=45
        )

        st.plotly_chart(fig, use_container_width=True)
        st.caption(f"Data saved permanently • Last updated: {data['time']} • Made by Amit Bhai")

    time.sleep(refresh)
