import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import time
import os

st.set_page_config(page_title="Amit Pro OI Terminal", layout="wide")

# Header
st.markdown("""
<style>
    .header { background: linear-gradient(90deg, #007bff, #00d4ff); padding: 16px 30px; border-radius: 0 20px 20px 0; 
              display: flex; align-items: center; color: white; font-size: 2rem; font-weight: bold; width: fit-content; 
              box-shadow: 0 4px 20px rgba(0,123,255,0.3); margin-bottom: 20px; }
    .logo { height: 60px; margin-right: 20px; border-radius: 12px; border: 3px solid white; }
    .live { color: #e74c3c; font-size: 1.8rem; font-weight: bold; animation: pulse 1.8s infinite; }
    @keyframes pulse { 0%,100% { opacity: 0.7; } 50% { opacity: 1; } }
    .stApp { background: #f8f9fa; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="header">
    <img src="https://cdn-icons-png.flaticon.com/512/2919/2919600.png" class="logo">
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
    st.markdown("<br><div class='live'>LIVE</div>", unsafe_allow_html=True)

refresh = st.slider("Refresh (sec)", 5, 20, 7)

# Session
@st.cache_resource(ttl=1800)
def get_session():
    s = requests.Session()
    s.headers.update({"User-Agent": "Mozilla/5.0", "Referer": "https://www.nseindia.com/option-chain"})
    s.get("https://www.nseindia.com")
    return s

session = get_session()

# History File
HISTORY_FILE = "oi_history.csv"
if os.path.exists(HISTORY_FILE):
    df_history = pd.read_csv(HISTORY_FILE)
else:
    df_history = pd.DataFrame(columns=["timestamp","index","expiry","price","ce_oi_raw","pe_oi_raw","net_oi_raw"])

placeholder = st.empty()

# Function to format OI (Lakhs or Crores)
def format_oi(value):
    if value >= 100:
        return f"{value/100:.2f} Cr"
    else:
        return f"{value:.1f} L"

while True:
    with placeholder.container():
        try:
            url = f"https://www.nseindia.com/api/option-chain-indices?symbol={index}"
            data = session.get(url, timeout=15).json()["records"]

            price = data["underlyingValue"]
            ts = datetime.strptime(data["timestamp"], "%d-%b-%Y %H:%M:%S")
            time_str = ts.strftime("%H:%M")

            expiries = data["expiryDates"]
            target = expiries[0] if expiry_type == "Current Week" else expiries[1] if expiry_type == "Next Week" and len(expiries)>1 else expiries[-1]

            ce_raw = pe_raw = 0
            for item in data["data"]:
                if item.get("expiryDate") == target:
                    if "CE" in item: ce_raw += item["CE"]["openInterest"]
                    if "PE" in item: pe_raw += item["PE"]["openInterest"]

            lot = 25 if index == "NIFTY" else 15 if index == "BANKNIFTY" else 25
            ce_lakh = round(ce_raw * lot / 100000, 1)
            pe_lakh = round(pe_raw * lot / 100000, 1)
            net_lakh = round((ce_raw - pe_raw) * lot / 100000, 1)

            # Save raw + formatted
            new_row = pd.DataFrame([{
                "timestamp": ts,
                "time": time_str,
                "index": index,
                "expiry": expiry_type,
                "price": round(price, 2),
                "ce_oi_raw": ce_lakh,
                "pe_oi_raw": pe_lakh,
                "net_oi_raw": net_lakh
            }])
            df_history = pd.concat([df_history, new_row], ignore_index=True)
            df_history.to_csv(HISTORY_FILE, index=False)

            st.success(f"Live • {index} • ₹{price:,.0f} • {time_str}")

        except:
            mask = (df_history["index"] == index) & (df_history["expiry"] == expiry_type)
            if df_history[mask].empty:
                st.info("Waiting for first data...")
                time.sleep(refresh)
                continue
            last = df_history[mask].iloc[-1]
            price = last["price"]
            time_str = pd.to_datetime(last["timestamp"]).strftime("%H:%M")
            ce_lakh = last["ce_oi_raw"]
            pe_lakh = last["pe_oi_raw"]
            net_lakh = last["net_oi_raw"]
            st.warning(f"Market Closed • Last: ₹{price:,.0f}")

        # Chart Data
        mask = (df_history["index"] == index) & (df_history["expiry"] == expiry_type)
        chart_df = df_history[mask].tail(80).copy()
        chart_df["time"] = pd.to_datetime(chart_df["timestamp"]).dt.strftime("%H:%M")

        # Final Chart
        fig = go.Figure()

        fig.add_trace(go.Scatter(x=chart_df["time"], y=chart_df["ce_oi_raw"],
            mode='lines+markers+text', name='CE OI',
            line=dict(color='#28a745', width=4),
            text=[format_oi(x) for x in chart_df["ce_oi_raw"]],
            textposition="top center", textfont=dict(size=13, color="#28a745", family="Arial Bold")))

        fig.add_trace(go.Scatter(x=chart_df["time"], y=chart_df["pe_oi_raw"],
            mode='lines+markers+text', name='PE OI',
            line=dict(color='#e74c3c', width=4),
            text=[format_oi(x) for x in chart_df["pe_oi_raw"]],
            textposition="bottom center", textfont=dict(size=13, color="#e74c3c", family="Arial Bold")))

        fig.add_trace(go.Scatter(x=chart_df["time"], y=chart_df["net_oi_raw"],
            mode='lines+markers+text', name='Net (CE-PE)',
            line=dict(color='#4361ee', width=5),
            text=[format_oi(x) if abs(x) >= 100 else f"{x:+.1f}L" for x in chart_df["net_oi_raw"]],
            textposition="top center", textfont=dict(size=14, color="#4361ee", family="Arial Black")))

        fig.add_trace(go.Scatter(x=chart_df["time"], y=chart_df["price"],
            name='Future Price', yaxis="y2",
            line=dict(color='#ffc107', width=4, dash='dot')))

        fig.update_layout(
            height=680,
            title=f"{index} • {expiry_type} • Live OI + Price Movement",
            title_x=0.5, title_font_size=20,
            legend=dict(orientation="h", y=1.02, x=1),
            xaxis=dict(tickangle=45),
            yaxis=dict(title="Open Interest"),
            yaxis2=dict(title="Price (₹)", overlaying="y", side="right", showgrid=False),
            hovermode="x unified"
        )

        st.plotly_chart(fig, use_container_width=True, key="pro_chart")

        # Current Values (with Cr/L)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("CE OI", format_oi(ce_lakh))
        c2.metric("PE OI", format_oi(pe_lakh))
        c3.metric("Net OI", format_oi(net_lakh) if abs(net_lakh) >= 100 else f"{net_lakh:+.1f}L")
        c4.metric("PCR", f"{round(pe_lakh/ce_lakh, 2) if ce_lakh>0 else 0:.2f}")

        st.caption("Made with ❤️ by Amit  • 100% NSE Live • Auto Cr/L Format • Data Saved Forever")

    time.sleep(refresh)
