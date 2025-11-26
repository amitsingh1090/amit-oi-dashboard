import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import time

st.set_page_config(page_title="Amit Pro OI Terminal", layout="wide", page_icon="Chart increasing")

# TradingTick Exact Look & Feel
st.markdown("""
<style>
    .stApp { background: #0f1117; font-family: 'Segoe UI', sans-serif; }
    .main { background: #0f1117; }
    h1 { color: #00ff88; text-align: center; font-size: 2.8rem; margin-bottom: 0; }
    .stMetric { background: #1a1d28; border-radius: 12px; padding: 12px; border: 1px solid #333; }
    .stMetric label { color: #00ff88 !important; font-size: 1rem !important; }
    .stMetric > div > div { color: white !important; font-weight: bold; font-size: 1.8rem !important; }
    .live-dot { color: #ff0066; font-size: 1.5rem; animation: blink 1.5s infinite; }
    @keyframes blink { 0%,100% { opacity: 0.4; } 50% { opacity: 1; } }
    .time-label { color: #888; font-size: 0.9rem; }
</style>
""", unsafe_allow_html=True)

st.markdown("<h1>AMIT'S PRO OI TERMINAL</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #888;'>NSE Official Live Data • Real-time OI & Price Tracking</p>", unsafe_allow_html=True)

# Sidebar
st.sidebar.image("https://i.imgur.com/7Y5X2hX.png", width=180)  # Optional logo
index = st.sidebar.selectbox("Index", ["NIFTY", "BANKNIFTY", "FINNIFTY"], index=0)
refresh = st.sidebar.slider("Refresh", 5, 15, 7)
st.sidebar.markdown(f"<div class='live-dot'>● LIVE</div>", unsafe_allow_html=True)

# Session
@st.cache_resource(ttl=3600)
def get_session():
    s = requests.Session()
    s.headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://www.nseindia.com"}
    return s
session = get_session()

def get_data():
    try:
        url = f"https://www.nseindia.com/api/option-chain-indices?symbol={index}"
        data = session.get(url, timeout=10).json()["records"]
        price = data["underlyingValue"]
        atm = round(price / 50) * 50
        lot = 25 if "NIFTY" in index else 15

        ce_oi = pe_oi = ce_ch = pe_ch = 0
        for item in data["data"]:
            if atm - 600 <= item["strikePrice"] <= atm + 600:
                if "CE" in item:
                    ce_oi += item["CE"]["openInterest"]
                    ce_ch += item["CE"]["changeinOpenInterest"]
                if "PE" in item:
                    pe_oi += item["PE"]["openInterest"]
                    pe_ch += item["PE"]["changeinOpenInterest"]

        return {
            "price": round(price, 2),
            "ce_oi": round(ce_oi * lot / 100000, 1),
            "pe_oi": round(pe_oi * lot / 100000, 1),
            "ce_ch": round(ce_ch * lot / 100000, 1),
            "pe_ch": round(pe_ch * lot / 100000, 1),
            "time": datetime.now().strftime("%H:%M:%S")
        }
    except:
        return None

# History
if "df" not in st.session_state:
    st.session_state.df = pd.DataFrame()

ph = st.empty()
while True:
    with ph.container():
        d = get_data()
        if not d:
            st.warning("Market Closed • Live from 9:15 AM")
            time.sleep(refresh)
            continue

        # Append
        st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([d])], ignore_index=True)
        st.session_state.df = st.session_state.df.tail(80)
        df = st.session_state.df

        # Header
        col1, col2, col3 = st.columns([1,1,1])
        with col2:
            st.markdown(f"<h2 style='text-align:center; color:#00ff88;'>{index} • {d['price']:,}</h2>", unsafe_allow_html=True)

        # Metrics
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("CE OI", f"{d['ce_oi']}L")
        c2.metric("PE OI", f"{d['pe_oi']}L")
        c3.metric("CE Change", f"{d['ce_ch']:+.1f}L", delta=f"{d['ce_ch']:+.1f}L")
        c4.metric("PE Change", f"{d['pe_ch']:+.1f}L", delta=f"{d['pe_ch']:+.1f}L")

        # TradingTick Exact Chart
        fig = go.Figure()
        fig.add_trace(go.Bar(x=df["time"], y=df["ce_ch"], name="CE Change", marker_color="#00ff88"))
        fig.add_trace(go.Bar(x=df["pe_ch"] < 0, y=df["pe_ch"], name="PE Change", marker_color="#ff0066"))
        fig.add_trace(go.Scatter(x=df["time"], y=df["price"], name="Price", yaxis="y2", line=dict(color="#ffd700", width=3)))

        fig.update_layout(
            template="plotly_dark",
            height=500,
            barmode="relative",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            xaxis=dict(tickangle=45, tickformat="%H:%M:%S"),
            yaxis=dict(title="OI Change (Lakhs)"),
            yaxis2=dict(title="Price", overlaying="y", side="right", showgrid=False)
        )
        st.plotly_chart(fig, use_container_width=True)

        # Footer
        st.markdown(f"<p style='text-align:center; color:#888; margin-top:20px;'>Updated: {d['time']} • Made with ❤️ by Amit Bhai</p>", unsafe_allow_html=True)

    time.sleep(refresh)
