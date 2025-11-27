import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import time
import os

st.set_page_config(page_title="Amit Pro OI Terminal", layout="wide")

# Clean Professional Theme
st.markdown("""
<style>
    .stApp { background: #f8f9fa; }
    .header { 
        background: linear-gradient(90deg, #007bff, #00c3ff); 
        padding: 15px 25px; 
        border-radius: 0 15px 15px 0; 
        display: flex; 
        align-items: center; 
        color: white; 
        font-size: 1.8rem; 
        font-weight: bold;
        width: fit-content;
    }
    .logo { height: 50px; margin-right: 15px; border-radius: 10px; }
    .live { color: #e74c3c; font-weight: bold; font-size: 1.5rem; }
</style>
""", unsafe_allow_html=True)

# Header - Top Left
st.markdown("""
<div class="header">
    <img src="https://i.imgur.com/7Y5X2hX.png" class="logo">
    AMIT'S PRO OI TERMINAL
</div>
""", unsafe_allow_html=True)

# Controls
col1, col2, col3 = st.columns([2, 2, 1])
with col1:
    index = st.selectbox("Index", ["NIFTY", "BANKNIFTY", "FINNIFTY"])
with col2:
    expiry_type = st.selectbox("Expiry", ["Current Week", "Next Week", "Monthly"])
with col3:
    st.markdown("<br><div class='live'>● LIVE</div>", unsafe_allow_html=True)

refresh = st.slider("Refresh (sec)", 5, 30, 8)

# Session & History
@st.cache_resource(ttl=3600)
def get_session():
    s = requests.Session()
    s.headers.update({"User-Agent": "Mozilla/5.0", "Referer": "https://www.nseindia.com"})
    s.get("https://www.nseindia.com")
    return s
session = get_session()

HISTORY_FILE = "oi_history.csv"
if os.path.exists(HISTORY_FILE):
    history_df = pd.read_csv(HISTORY_FILE)
else:
    history_df = pd.DataFrame()

def fetch_data():
    try:
        url = f"https://www.nseindia.com/api/option-chain-indices?symbol={index}"
        data = session.get(url, timeout=12).json()["records"]
        price = data["underlyingValue"]
        timestamp = datetime.strptime(data["timestamp"], "%d-%b-%Y %H:%M:%S")
        time_str = timestamp.strftime("%H:%M")

        expiries = [e["expiryDate"] for e in data["expiryDates"]]
        target = expiries[0] if expiry_type == "Current Week" else expiries[1] if "Next Week" in expiry_type else expiries[-1]

        ce_oi = pe_oi = ce_ch = pe_ch = 0
        for item in data["data"]:
            if item.get("expiryDate") == target:
                if "CE" in item:
                    ce_oi += item["CE"]["openInterest"]
                    ce_ch += item["CE"]["changeinOpenInterest"]
                if "PE" in item:
                    pe_oi += item["PE"]["openInterest"]
                    pe_ch += item["PE"]["changeinOpenInterest"]

        lot = 25 if index == "NIFTY" else 15 if index == "BANKNIFTY" else 25
        net_diff = (ce_ch - pe_ch) * lot / 100000

        result = {
            "time": time_str,
            "price": round(price, 2),
            "ce_oi": round(ce_oi * lot / 100000, 1),
            "pe_oi": round(pe_oi * lot / 100000, 1),
            "ce_change": round(ce_ch * lot / 100000, 1),
            "pe_change": round(pe_ch * lot / 100000, 1),
            "net_diff": round(net_diff, 1),
            "timestamp": timestamp
        }

        # Save
        new_row = pd.DataFrame([{**result, "index": index, "expiry": expiry_type}])
        global history_df
        history_df = pd.concat([history_df, new_row], ignore_index=True)
        history_df.to_csv(HISTORY_FILE, index=False)
        return result
    except:
        return None

# Main Layout
left_col, right_col = st.columns([30, 70])

ph = st.empty()
while True:
    with ph.container():
        data = fetch_data()
        if not data:
            st.info("Market Closed / Loading History...")
            time.sleep(refresh)
            continue

        # Filter history
        mask = (history_df["index"] == index) & (history_df["expiry"] == expiry_type)
        df = history_df[mask].tail(100).copy()
        df["time"] = pd.to_datetime(df["timestamp"]).dt.strftime("%H:%M")

        # LEFT: OI Bar Chart
        with left_col:
            st.markdown("#### OI (Lakhs)")
            fig_bar = go.Figure()
            fig_bar.add_trace(go.Bar(y=["CE"], x=[data["ce_oi"]], name="CE OI", marker_color="#28a745", text=[data["ce_oi"]], textposition="outside"))
            fig_bar.add_trace(go.Bar(y=["PE"], x=[-data["pe_oi"]], name="PE OI", marker_color="#e74c3c", text=[data["pe_oi"]], textposition="outside"))
            fig_bar.update_layout(height=300, barmode="relative", showlegend=False, yaxis=dict(showticklabels=False))
            st.plotly_chart(fig_bar, use_container_width=True)

            # Current Values
            st.metric("CE OI", f"{data['ce_oi']}L")
            st.metric("PE OI", f"{data['pe_oi']}L")
            st.metric("Net Change", f"{data['net_diff']:+.1f}L")

        # RIGHT: Multi-Line Dual Axis Chart
        with right_col:
            st.markdown(f"#### {index} • ₹{data['price']:,} • {data['time']} • {expiry_type}")
            fig = go.Figure()

            fig.add_trace(go.Scatter(x=df["time"], y=df["ce_change"], mode="lines+markers", name="CE Change", line=dict(color="#28a745", width=3)))
            fig.add_trace(go.Scatter(x=df["time"], y=df["pe_change"], mode="lines+markers", name="PE Change", line=dict(color="#e74c3c", width=3)))
            fig.add_trace(go.Scatter(x=df["time"], y=df["net_diff"], mode="lines+markers", name="CE-PE Diff", line=dict(color="#4361ee", width=4)))
            fig.add_trace(go.ScFut(x=df["time"], y=df["price"], name="Future Price", yaxis="y2", line=dict(color="#ffc107", width=4, dash="dot")))

            fig.update_layout(
                height=600,
                legend=dict(orientation="h", y=1.02, x=1),
                xaxis_tickangle=45,
                yaxis=dict(title="Change in OI (Lakhs)"),
                yaxis2=dict(title="Price", overlaying="y", side="right", showgrid=False)
            )
            st.plotly_chart(fig, use_container_width=True)

        st.caption("Data saved permanently • 100% NSE Official • Made by Amit Bhai")

    time.sleep(refresh)
