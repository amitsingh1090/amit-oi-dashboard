import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import time
import os

st.set_page_config(page_title="Amit Pro OI Terminal", layout="wide")

# Fixed Logo + Header
st.markdown("""
<style>
    .stApp { background: #f8f9fa; }
    .header {
        background: linear-gradient(90deg, #007bff, #00c3ff);
        padding: 15px 30px;
        border-radius: 0 20px 20px 0;
        display: flex;
        align-items: center;
        color: white;
        font-size: 2rem;
        font-weight: bold;
        width: fit-content;
        box-shadow: 0 4px 20px rgba(0,123,255,0.4);
    }
    .logo { height: 58px; margin-right: 20px; border-radius: 12px; border: 3px solid white; }
    .live { color: #e74c3c; font-weight: bold; font-size: 1.8rem; animation: pulse 1.8s infinite; }
    @keyframes pulse { 0%,100% { opacity: 0.7; } 50% { opacity: 1; } }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="header">
    <img src="https://cdn-icons-png.flaticon.com/512/2919/2919600.png" class="logo">
    AMIT'S PRO OI TERMINAL
</div>
""", unsafe_allow_html=True)

# Controls
c1, c2, c3 = st.columns([2,2,1])
with c1:
    index = st.selectbox("Index", ["NIFTY", "BANKNIFTY", "FINNIFTY"])
with c2:
    expiry_type = st.selectbox("Expiry", ["Current Week", "Next Week", "Monthly"])
with c3:
    st.markdown("<br><div class='live'>LIVE</div>", unsafe_allow_html=True)

refresh = st.slider("Refresh (sec)", 5, 20, 7)

# PROPER NSE SESSION (yeh sabse important fix hai)
@st.cache_resource(ttl=1800)
def get_nse_session():
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.nseindia.com/option-chain",
        "X-Requested-With": "XMLHttpRequest"
    })
    # Warm-up request (must)
    try:
        session.get("https://www.nseindia.com", timeout=10)
        time.sleep(1)
        session.get("https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY", timeout=10)
    except:
        pass
    return session

session = get_nse_session()

# History
HISTORY_FILE = "oi_history.csv"
if os.path.exists(HISTORY_FILE):
    history_df = pd.read_csv(HISTORY_FILE)
else:
    history_df = pd.DataFrame()

def get_live_data():
    try:
        url = f"https://www.nseindia.com/api/option-chain-indices?symbol={index}"
        json_data = session.get(url, timeout=15).json()
        records = json_data["records"]
        
        price = records["underlyingValue"]
        timestamp = datetime.strptime(records["timestamp"], "%d-%b-%Y %H:%M:%S")
        time_str = timestamp.strftime("%H:%M")

        # Expiry logic
        expiries = records["expiryDates"]
        if expiry_type == "Current Week":
            target = expiries[0]
        elif expiry_type == "Next Week" and len(expiries) > 1:
            target = expiries[1]
        else:
            target = expiries[-1]

        ce_oi = pe_oi = ce_ch = pe_ch = 0
        for item in records["data"]:
            if item.get("expiryDate") == target:
                if "CE" in item:
                    ce_oi += item["CE"]["openInterest"]
                    ce_ch += item["CE"]["changeinOpenInterest"]
                if "PE" in item:
                    pe_oi += item["PE"]["openInterest"]
                    pe_ch += item["PE"]["changeinOpenInterest"]

        lot = 25 if index == "NIFTY" else 15 if index == "BANKNIFTY" else 25

        result = {
            "timestamp": timestamp,
            "time": time_str,
            "price": round(price, 2),
            "ce_oi": round(ce_oi * lot / 100000, 1),
            "pe_oi": round(pe_oi * lot / 100000, 1),
            "ce_change": round(ce_ch * lot / 100000, 1),
            "pe_change": round(pe_ch * lot / 100000, 1),
            "net_diff": round((ce_ch - pe_ch) * lot / 100000, 1)
        }

        # Save history
        new_row = pd.DataFrame([{**result, "index": index, "expiry": expiry_type}])
        global history_df
        history_df = pd.concat([history_df, new_row], ignore_index=True)
        history_df.to_csv(HISTORY_FILE, index=False)

        return result
    except Exception as e:
        return None

# Layout
left, right = st.columns([3, 7])
ph = st.empty()

while True:
    with ph.container():
        data = get_live_data()

        # Always show latest available data
        mask = (history_df["index"] == index) & (history_df["expiry"] == expiry_type)
        df = history_df[mask].copy()
        if not df.empty:
            df["time"] = pd.to_datetime(df["timestamp"]).dt.strftime("%H:%M")
            df = df.tail(100)

        current = data if data else (df.iloc[-1].to_dict() if not df.empty else None)

        if not current:
            st.error("No data yet. Waiting for first update...")
            time.sleep(refresh)
            continue

        # LEFT: OI Bar
        with left:
            st.markdown("#### OI (Lakhs)")
            fig_bar = go.Figure()
            fig_bar.add_trace(go.Bar(y=["CE"], x=[current["ce_oi"]], marker_color="#28a745",
                                   text=[current["ce_oi"]], textposition="outside"))
            fig_bar.add_trace(go.Bar(y=["PE"], x=[-current["pe_oi"]], marker_color="#e74c3c",
                                   text=[current["pe_oi"]], textposition="outside"))
            fig_bar.update_layout(height=380, barmode="relative", showlegend=False,
                                yaxis=dict(showticklabels=False))
            st.plotly_chart(fig_bar, use_container_width=True)

            st.metric("CE OI", f"{current['ce_oi']}L")
            st.metric("PE OI", f"{current['pe_oi']}L")
            st.metric("Net Diff", f"{current['net_diff']:+}L")

        # RIGHT: Multi-Line Chart
        with right:
            st.markdown(f"#### {index} • ₹{current['price']:,} • {current['time']} • {expiry_type}")
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df["time"], y=df["ce_change"], name="CE Change", line=dict(color="#28a745", width=3)))
            fig.add_trace(go.Scatter(x=df["time"], y=df["pe_change"], name="PE Change", line=dict(color="#e74c3c", width=3)))
            fig.add_trace(go.Scatter(x=df["time"], y=df["net_diff"], name="Net (CE-PE)", line=dict(color="#4361ee", width=4)))
            fig.add_trace(go.Scatter(x=df["time"], y=df["price"], name="Future Price", yaxis="y2",
                                   line=dict(color="#ffc107", width=4, dash="dot")))
            fig.update_layout(height=580, legend=dict(orientation="h", y=1.02, x=1),
                            yaxis=dict(title="Change in OI (Lakhs)"),
                            yaxis2=dict(title="Price", overlaying="y", side="right"))
            st.plotly_chart(fig, use_container_width=True)

        st.caption("Made by Amit Bhai • 100% NSE Live Data")

    time.sleep(refresh)
