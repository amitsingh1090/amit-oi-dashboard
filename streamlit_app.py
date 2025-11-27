import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import time

st.set_page_config(page_title="Amit Pro OI Terminal", layout="wide", page_icon="Chart increasing")

# Clean Professional UI
st.markdown("""
<style>
    .stApp { background: #0f1117; }
    h1 { color: #00ff88; text-align: center; font-size: 2.8rem; margin: 0; }
    .metric-box { background: #1a1d28; padding: 15px; border-radius: 12px; border: 1px solid #333; }
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

# NSE Session with proper headers
@st.cache_resource(ttl=3600)
def get_session():
    s = requests.Session()
    s.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
        "Referer": "https://www.nseindia.com/option-chain",
        "X-Requested-With": "XMLHttpRequest"
    })
    # First hit to get cookies
    s.get("https://www.nseindia.com/option-chain")
    return s

session = get_session()

def fetch_oi_data():
    try:
        url = f"https://www.nseindia.com/api/option-chain-indices?symbol={index}"
        resp = session.get(url, timeout=10)
        data = resp.json()
        
        underlying = data["records"]["underlyingValue"]
        timestamp = data["records"]["timestamp"]  # This is NSE server time!
        nse_time = datetime.strptime(timestamp, "%d-%b-%tq%Y %H:%M:%S").strftime("%H:%M:%S")
        
        total_ce_oi = total_pe_oi = total_ce_ch = total_pe_ch = 0
        
        for item in data["records"]["data"]:
            if "CE" in item:
                total_ce_oi += item["CE"]["openInterest"]
                total_ce_ch += item["CE"]["changeinOpenInterest"]
            if "PE" in item:
                total_pe_oi += item["PE"]["openInterest"]
                total_pe_ch += item["PE"]["changeinOpenInterest"]

        lot_size = 25 if index == "NIFTY" else 15 if index == "BANKNIFTY" else 
