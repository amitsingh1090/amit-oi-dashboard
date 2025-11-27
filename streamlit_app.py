import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import time
import os

st.set_page_config(page_title="Amit Pro OI Terminal", layout="wide")

# Clean Header
st.markdown("""
<style>
    .header { background: linear-gradient(90deg, #007bff, #00d4ff); padding: 16px 30px; border-radius: 0 20px 20px 0; 
              display: flex; align-items: center; color: white; font-size: 2rem; font-weight: bold; width: fit-content; 
              box-shadow: 0 4px 20px rgba(0,123,255,0.3); margin-bottom: 20px; }
    .logo { height: 60px; margin-right: 20px; border-radius: 3px solid white; border-radius: 12px; }
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
    s.headers.update({
        "User-Agent": "Mozilla/5.0", "Referer": "https://www.nseindia.com/option-chain"
    })
    s.get("https://www.nseindia.com")
    return s

session = get_session()

# History
HISTORY_FILE = "oi_history.csv"
if os.path.exists(HISTORY_FILE):
    df_history = pd.read_csv(HISTORY_FILE)
else:
    df_history = pd.DataFrame(columns=["timestamp","index","expiry","price","ce_oi","pe_oi","net_oi"])

placeholder = st.empty()

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

            ce_oi = pe_oi = 0
            for item in data["data"]:
                if item.get("expiryDate") == target:
                    if "CE" in item: ce_oi += item["CE"]["openInterest"]
                    if "PE" in item: pe_oi += item["PE"]["openInterest"]

            lot = 25 if index == "NIFTY" else 15 if index == "BANKNIFTY" else 25
            ce_lakh = round(ce_oi * lot / 100000, 1)
            pe_lakh = round(pe_oi * lot / 100000, 1)
            net_oi = round((ce_oi - pe_oi) * lot / 100000, 1)

            new_row = pd.DataFrame([{
                "timestamp": ts,
                "time": time_str,
                "index": index,
                "expiry": expiry_type,
                "price": round(price, 2),
                "ce_oi": ce_lakh,
                "pe_oi": pe_lakh,
                "net_oi": net_oi
            }])

            global df_history
            df_history = pd.concat([df_history, new_row], ignore_index=True)
            df_history.to_csv(HISTORY_FILE, index=False)

            st.success(f"Live • {index} • ₹{price:,.0f} • {time_str} • {expiry_type}")

        except:
            mask = (df_history["index"] == index) & (df_history["expiry"] == expiry_type)
            if df_history[mask].empty:
                st.info("Waiting for data...")
                time.sleep(refresh)
                continue
            last = df_history[mask].iloc[-1]
            price = last["price"]
            time_str = pd.to_datetime(last["timestamp"]).strftime("%H:%M")
            st.warning(f"Market Closed • Last: ₹{price:,.0f} • {time_str}")

        # Filter data for chart
        mask = (df_history["index"] == index) & (df_history["expiry"] == expiry_type)
        chart_df = df_history[mask].tail(80).copy()
        chart_df["time"] = pd.to_datetime(chart_df["timestamp"]).dt.strftime("%H:%M")

        # === FINAL DUAL-AXIS MULTI-LINE CHART (TradingTick Style) ===
        fig = go.Figure()

        # CE OI Line
        fig.add_trace(go.Scatter(
            x=chart_df["time"], y=chart_df["ce_oi"],
            mode='lines+markers+text',
            name='CE OI',
            line=dict(color='#28a745', width=4),
            marker=dict(size=8),
            text=chart_df["ce_oi"],
            textposition="top center",
            textfont=dict(size=12, color="#28a745")
        ))

        # PE OI Line
        fig.add_trace(go.Scatter(
            x=chart_df["time"], y=chart_df["pe_oi"],
            mode='lines+markers+text',
            name='PE OI',
            line=dict(color='#e74c3c', width=4),
            marker=dict(size=8),
            text=chart_df["pe_oi"],
            textposition="bottom center",
            textfont=dict(size=12, color="#e74c3c")
        ))

        # Net (CE-PE) Line
        fig.add_trace(go.Scatter(
            x=chart_df["time"], y=chart_df["net_oi"],
            mode='lines+markers+text',
            name='Net OI (CE-PE)',
            line=dict(color='#4361ee', width=5),
            marker=dict(size=10),
            text=chart_df["net_oi"],
            textposition="top center",
            textfont=dict(size=13, color="#4361ee", family="Arial Black")
        ))

        # Future Price - Right Axis (Dotted Yellow)
        fig.add_trace(go.Scatter(
            x=chart_df["time"], y=chart_df["price"],
            mode='lines',
            name='Future Price',
            yaxis="y2",
            line=dict(color='#ffc107', width=4, dash='dot')
        ))

        fig.update_layout(
            height=650,
            title=dict(text=f"{index} • {expiry_type} • Live OI + Price Movement", x=0.5, font=dict(size=18)),
            plot_bgcolor="white",
            paper_bgcolor="white",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            xaxis=dict(title="Time", tickangle=45),
            yaxis=dict(title="Open Interest (Lakhs)", side="left", gridcolor="#eee"),
            yaxis2=dict(title="Future Price (₹)", overlaying="y", side="right", showgrid=False),
            hovermode="x unified",
            margin=dict(l=60, r=60, t=80, b=60)
        )

        st.plotly_chart(fig, use_container_width=True, key="final_chart")

        # Current Values
        col_a, col_b, col_c, col_d = st.columns(4)
        col_a.metric("CE OI", f"{ce_lakh}L", "+ve Bullish")
        col_b.metric("PE OI", f"{pe_lakh}L", "-ve Bearish")
        col_c.metric("Net OI", f"{net_oi:+}L", "CE-PE")
        col_d.metric("PCR", f"{round(pe_lakh/ce_lakh, 2) if ce_lakh>0 else 0:.2f}")

        st.caption("Made with passion by Amit Bhai • 100% NSE Live • Data Saved Forever")

    time.sleep(refresh)
