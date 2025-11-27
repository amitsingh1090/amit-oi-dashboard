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
    .header { background: linear-gradient(90deg, #007bff, #00d4ff); padding: 18px 35px; border-radius: 0 25px 25px 0; 
              display: flex; align-items: center; color: white; font-size: 2.1rem; font-weight: bold; width: fit-content; 
              box-shadow: 0 6px 25px rgba(0,123,255,0.4); margin-bottom: 25px; }
    .logo { height: 65px; margin-right: 22px; border-radius: 12px; border: 4px solid white; }
    .live { color: #e74c3c; font-size: 2rem; font-weight: bold; animation: pulse 1.5s infinite; }
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
index = st.selectbox("Index", ["NIFTY", "BANKNIFTY", "FINNIFTY"])
expiry_type = st.selectbox("Expiry", ["Current Week", "Next Week", "Monthly"])
refresh = st.slider("Refresh (sec)", 5, 30, 8)

col1, col2, col3 = st.columns([5, 5, 2])
with col3:
    st.markdown("<br><div class='live'>LIVE</div>", unsafe_allow_html=True)

# Session
@st.cache_resource(ttl=1800)
def get_session():
    s = requests.Session()
    s.headers.update({"User-Agent": "Mozilla/5.0", "Referer": "https://www.nseindia.com/option-chain"})
    s.get("https://www.nseindia.com")
    return s
session = get_session()

# History File - AB PURA DATA SAVE HOGA (market band hone ke baad bhi dikhega)
HISTORY_FILE = "oi_history.csv"
if os.path.exists(HISTORY_FILE):
    df_history = pd.read_csv(HISTORY_FILE)
    df_history["timestamp"] = pd.to_datetime(df_history["timestamp"])
else:
    df_history = pd.DataFrame(columns=["timestamp","index","expiry","price","ce_oi","pe_oi","ce_ch","pe_ch","net_diff"])

def format_oi(val):
    if abs(val) >= 100:
        return f"{val/100:.2f} Cr"
    else:
        return f"{val:.1f} L"

placeholder = st.empty()

while True:
    with placeholder.container():
        current_time = datetime.now()
        live_data = None

        # Try to fetch live data
        try:
            url = f"https://www.nseindia.com/api/option-chain-indices?symbol={index}"
            resp = session.get(url, timeout=15).json()["records"]
            price = resp["underlyingValue"]
            ts = datetime.strptime(resp["timestamp"], "%d-%b-%Y %H:%M:%S")
            time_str = ts.strftime("%H:%M")

            expiries = resp["expiryDates"]
            target = expiries[0] if expiry_type == "Current Week" else expiries[1] if "Next Week" in expiry_type and len(expiries)>1 else expiries[-1]

            ce_oi = pe_oi = ce_ch = pe_ch = 0
            for item in resp["data"]:
                if item.get("expiryDate") == target:
                    if "CE" in item:
                        ce_oi += item["CE"]["openInterest"]
                        ce_ch += item["CE"]["changeinOpenInterest"]
                    if "PE" in item:
                        pe_oi += item["PE"]["openInterest"]
                        pe_ch += item["PE"]["changeinOpenInterest"]

            lot = 25 if index == "NIFTY" else 15
            ce_lakh = round(ce_oi * lot / 100000, 1)
            pe_lakh = round(pe_oi * lot / 100000, 1)
            ce_change = round(ce_ch * lot / 100000, 1)
            pe_change = round(pe_ch * lot / 100000, 1)
            net_diff = round((ce_ch - pe_ch) * lot / 100000, 1)

            live_data = {
                "timestamp": ts, "price": price, "ce_oi": ce_lakh, "pe_oi": pe_lakh,
                "ce_ch": ce_change, "pe_ch": pe_change, "net_diff": net_diff
            }

            # Save data
            new_row = pd.DataFrame([{**live_data, "index": index, "expiry": expiry_type}])
            df_history = pd.concat([df_history, new_row], ignore_index=True)
            df_history.to_csv(HISTORY_FILE, index=False)

            st.success(f"Live • {index} • ₹{price:,.0f} • {time_str}")

        except:
            st.warning("Market Closed • Showing Last Saved Data")

        # Use last available data
        mask = (df_history["index"] == index) & (df_history["expiry"] == expiry_type)
        if df_history[mask].empty:
            st.info("No data yet. Waiting for market open...")
            time.sleep(refresh)
            continue

        last_row = df_history[mask].iloc[-1]
        ce_lakh = last_row["ce_oi"]
        pe_lakh = last_row["pe_oi"]
        net_diff = last_row["net_diff"]
        price = last_row["price"]

        # Filter history for chart
        chart_df = df_history[mask].tail(100).copy()
        chart_df["time"] = chart_df["timestamp"].dt.strftime("%H:%M")

        # LEFT: OI BAR (ab bilkul clear dikhega)
        left, right = st.columns([3, 7])

        with left:
            st.markdown("#### Open Interest")
            max_val = max(ce_lakh, pe_lakh, 50)
            fig_bar = go.Figure()
            fig_bar.add_trace(go.Bar(
                y=["OI"], x=[ce_lakh], name="CE", marker_color="#28a745",
                text=format_oi(ce_lakh), textposition="outside", textfont_size=14
            ))
            fig_bar.add_trace(go.Bar(
                y=["OI"], x=[-pe_lakh], name="PE", marker_color="#e74c3c",
                text=format_oi(pe_lakh), textposition="outside", textfont_size=14
            ))
            fig_bar.update_layout(
                height=500, barmode="relative", showlegend=False,
                yaxis=dict(showticklabels=False),
                xaxis=dict(range=[-max_val*1.2, max_val*1.2], showgrid=False, zeroline=True, zerolinecolor="black", zerolinewidth=2),
                margin=dict(t=50, l=20, r=20, b=20)
            )
            st.plotly_chart(fig_bar, use_container_width=True)

            col1, col2 = st.columns(2)
            col1.metric("CE OI", format_oi(ce_lakh))
            col2.metric("PE OI", format_oi(pe_lakh))

        # RIGHT: Full Change Chart
        with right:
            st.markdown("#### CE/PE Change • Net Difference • Future Price")
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=chart_df["time"], y=chart_df["ce_ch"], name="CE Change", line=dict(color="#28a745", width=4)))
            fig.add_trace(go.Scatter(x=chart_df["time"], y=chart_df["pe_ch"], name="PE Change", line=dict(color="#e74c3c", width=4)))
            fig.add_trace(go.Scatter(x=chart_df["time"], y=chart_df["net_diff"], name="Net (CE-PE)", line=dict(color="#4361ee", width=5)))
            fig.add_trace(go.Scatter(x=chart_df["time"], y=chart_df["price"], name="Future Price", yaxis="y2",
                                   line=dict(color="#ffc107", width=4, dash="dot")))

            fig.update_layout(
                height=500,
                legend=dict(orientation="h", y=1.02, x=1),
                xaxis_tickangle=45,
                yaxis=dict(title="Change in OI (Lakhs)"),
                yaxis2=dict(title="Price (₹)", overlaying="y", side="right"),
                hovermode="x unified"
            )
            st.plotly_chart(fig, use_container_width=True)

        # Bottom metrics
        col1, col2, col3 = st.columns(3)
        col1.metric("Net CE-PE Change", f"{net_diff:+.1f}L", delta=f"{net_diff:+.1f}L")
        col2.metric("Current Price", f"₹{price:,.0f}")
        col3.metric("PCR", f"{round(pe_lakh/ce_lakh, 2) if ce_lakh>0 else 0:.2f}")

        st.caption("Made by Amit Bhai • 100% NSE Live • Data Saved Forever • Works After Market Hours Too!")

    time.sleep(refresh)
