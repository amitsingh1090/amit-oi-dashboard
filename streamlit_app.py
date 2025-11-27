import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import time

st.set_page_config(page_title="Amit Pro OI Terminal", layout="wide", page_icon="Chart increasing")

# Clean Pro UI
st.markdown("""
<style>
    .stApp { background: #0f1117; }
    h1 { color: #00ff88; text-align: center; font-size: 2.8rem; margin: 0; }
    .stMetric { background: #1a1d28; padding: 15px; border-radius: 12px; border: 1px solid #333; }
    .stMetric label { color: #00ff88 !important; font-size: 1rem !important; }
    .stMetric > div > div { color: white !important; font-weight: bold; font-size: 1.9rem !important; }
    .live { color: #ff0066; font-weight: bold; animation: pulse 2s infinite; }
    @keyframes pulse { 0% { opacity: 0.6; } 50% { opacity: 1; } 100% { opacity: 0.6; } }
</style>
""", unsafe_allow_html=True)

st.markdown("<h1>AMIT'S PRO OI TERMINAL</h1>", unsafe_allow_html=True)

# Sidebar
index = st.sidebar.selectbox("Index", ["NIFTY", "BANKNIFTY", "FINNIFTY"])
refresh = st.sidebar.slider("Refresh (sec)", 5, 15, 7)
st.sidebar.markdown("<div class='live'>● LIVE</div>", unsafe_allow_html=True)

# NSE Session
@st.cache_resource(ttl=3600)
def get_session():
    s = requests.Session()
    s.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://www.nseindia.com/option-chain",
    })
    s.get("https://www.nseindia.com")  # Warm up
    return s

session = get_session()

def fetch_oi_data():
    try:
        url = f"https://www.nseindia.com/api/option-chain-indices?symbol={index}"
        resp = session.get(url, timeout=12).json()
        
        underlying = resp["records"]["underlyingValue"]
        timestamp = resp["records"]["timestamp"]
        nse_time = datetime.strptime(timestamp, "%d-%b-%Y %H:%M:%S").strftime("%H:%M:%S")
        
        total_ce_oi = total_pe_oi = total_ce_ch = total_pe_ch = 0
        for item in resp["records"]["data"]:
            if "CE" in item:
                total_ce_oi += item["CE"]["openInterest"]
                total_ce_ch += item["CE"]["changeinOpenInterest"]
            if "PE" in item:
                total_pe_oi += item["PE"]["openInterest"]
                total_pe_ch += item["PE"]["changeinOpenInterest"]

        # Correct lot size
        lot_size = 25 if index == "NIFTY" else 15 if index == "BANKNIFTY" else 25

        return {
            "price": round(underlying, 2),
            "ce_oi": round(total_ce_oi * lot_size / 100000, 1),
            "pe_oi": round(total_pe_oi * lot_size / 100000, 1),
            "ce_change": round(total_ce_ch * lot_size / 100000, 1),
            "pe_change": round(total_pe_ch * lot_size / 100000, 1),
            "time": nse_time
        }
    except:
        return None

# History init
if "history" not in st.session_state:
    st.session_state.history = pd.DataFrame(columns=["price","ce_oi","pe_oi","ce_change","pe_change","time"])

ph = st.empty()
while True:
    with ph.container():
        data = fetch_oi_data()
        if not data:
            st.warning("Loading data from NSE...")
            time.sleep(refresh)
            continue

        # Append data
        new_row = pd.DataFrame([data])
        st.session_state.history = pd.concat([st.session_state.history, new_row], ignore_index=True)
        st.session_state.history = st.session_state.history.tail(100)
        df = st.session_state.history

        # Display
        st.markdown(f"### {index} • ₹{data['price']:,} • NSE Time: {data['time']}")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("CE OI", f"{data['ce_oi']}L")
        c2.metric("PE OI", f"{data['pe_oi']}L")
        c3.metric("CE Change", f"{data['ce_change']:+.1f}L", delta=f"{data['ce_change']:+.1f}L")
        c4.metric("PE Change", f"{data['pe_change']:+.1f}L", delta=f"{data['pe_change']:+.1f}L")

        # Chart
        fig = go.Figure()
        fig.add_trace(go.Bar(x=df["time"], y=df["ce_change"], name="CE Change", marker_color="#00ff88"))
        fig.add_trace(go.Bar(x=df["time"], y=df["pe_change"], name="PE Change", marker_color="#ff0066"))
        fig.add_trace(go.Scatter(x=df["time"], y=df["price"], name="Price", yaxis="y2", line=dict(color="#ffd700", width=3)))

        fig.update_layout(
            template="plotly_dark",
            height=520,
            barmode="relative",
            legend=dict(orientation="h", y=1.02, x=1),
            xaxis=dict(tickangle=45, type="category"),
            yaxis=dict(title="OI Change (Lakhs)"),
            yaxis2=dict(title="Price", overlaying="y", side="right", showgrid=False)
        )
        st.plotly_chart(fig, use_container_width=True)

        st.caption(f"Last Updated: {data['time']} • 100% NSE Official Data • Made by Amit Bhai")

    time.sleep(refresh)
