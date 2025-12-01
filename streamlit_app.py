import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import time
import os

st.set_page_config(page_title="Amit Pro OI Terminal", layout="wide")

# === HEADER ===
st.markdown("""
<style>
    .header { background: linear-gradient(90deg, #007bff, #00ff9d); padding: 20px 40px; border-radius: 0 30px 30px 0; 
              display: flex; align-items: center; color: white; font-size: 2.4rem; font-weight: bold; width: fit-content; 
              box-shadow: 0 8px 30px rgba(0,123,255,0.5); margin-bottom: 30px; }
    .logo { height: 70px; margin-right: 25px; border-radius: 15px; border: 5px solid white; }
    .live { color: #ff0066; font-size: 2.2rem; font-weight: bold; animation: pulse 1.4s infinite; }
    @keyframes pulse { 0%,100% { opacity: 0.7; } 50% { opacity: 1; } }
    .stApp { background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="header">
    <img src="https://cdn-icons-png.flaticon.com/512/2919/2919600.png" class="logo">
    AMIT'S PRO OI TERMINAL
</div>
""", unsafe_allow_html=True)

# Tabs
tab1, tab2 = st.tabs(["Live OI Dashboard", "All Indices OI Summary"])

with tab1:
    col1, col2, col3 = st.columns([3, 3, 1])
    with col1:
        index = st.selectbox("Select Index", ["NIFTY", "BANKNIFTY", "FINNIFTY"])
    with col2:
        expiry_type = st.selectbox("Expiry", ["Current Week", "Next Week", "Monthly"])
    with col3:
        st.markdown("<br><div class='live'>LIVE</div>", unsafe_allow_html=True)

    refresh = st.slider("Refresh (sec)", 5, 30, 10, key="ref")

with tab2:
    st.markdown("### Live Open Interest Summary - All Indices")
    refresh_all = st.checkbox("Auto Refresh Every 15 Sec", value=True)

# Session
@st.cache_resource(ttl=1800)
def get_session():
    s = requests.Session()
    s.headers.update({"User-Agent": "Mozilla/5.0", "Referer": "https://www.nseindia.com/option-chain"})
    s.get("https://www.nseindia.com", timeout=10)
    return s
session = get_session()

HISTORY_FILE = "oi_history.csv"
if os.path.exists(HISTORY_FILE):
    df_history = pd.read_csv(HISTORY_FILE)
    df_history["timestamp"] = pd.to_datetime(df_history["timestamp"])
else:
    df_history = pd.DataFrame(columns=["timestamp","index","expiry","price","ce_oi","pe_oi","ce_ch","pe_ch","net_diff"])

def format_oi(val):
    if abs(val) >= 100:
        return f"{val/100:.2f} Cr"
    return f"{val:.1f} L"

def get_oi_data(symbol):
    try:
        url = f"https://www.nseindia.com/api/option-chain-indices?symbol={symbol}"
        data = session.get(url, timeout=12).json()["records"]
        price = data["underlyingValue"]
        expiries = data["expiryDates"]
        target = expiries[0]  # Current week

        ce_oi = pe_oi = ce_ch = pe_ch = 0
        for item in data["data"]:
            if item.get("expiryDate") == target:
                if "CE" in item:
                    ce_oi += item["CE"]["openInterest"]
                    ce_ch += item["CE"]["changeinOpenInterest"]
                if "PE" in item:
                    pe_oi += item["PE"]["openInterest"]
                    pe_ch += item["PE"]["changeinOpenInterest"]

        lot = 25 if symbol == "NIFTY" else 15
        return {
            "price": round(price),
            "ce_oi": round(ce_oi * lot / 100000, 1),
            "pe_oi": round(pe_oi * lot / 100000, 1),
            "net_ch": round((ce_ch - pe_ch) * lot / 100000, 1),
            "pcr": round((pe_oi / ce_oi) if ce_oi > 0 else 0, 2)
        }
    except:
        return None

# Main Dashboard Loop
placeholder = st.empty()

while True:
    with placeholder.container():
        # === TAB 1: Single Index Dashboard ===
        with tab1:
            try:
                url = f"https://www.nseindia.com/api/option-chain-indices?symbol={index}"
                data = session.get(url, timeout=15).json()["records"]
                price = data["underlyingValue"]
                ts = datetime.strptime(data["timestamp"], "%d-%b-%Y %H:%M:%S")

                expiries = data["expiryDates"]
                target = expiries[0] if expiry_type == "Current Week" else expiries[1] if len(expiries)>1 else expiries[0]

                ce_oi = pe_oi = ce_ch = pe_ch = 0
                for item in data["data"]:
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
                net_change = round((ce_ch - pe_ch) * lot / 100000, 1)

                # Save
                new_row = pd.DataFrame([{
                    "timestamp": ts, "index": index, "expiry": expiry_type,
                    "price": price, "ce_oi": ce_lakh, "pe_oi": pe_lakh,
                    "ce_ch": round(ce_ch * lot / 100000, 1),
                    "pe_ch": round(pe_ch * lot / 100000, 1),
                    "net_diff": net_change
                }])
                global df_history
                df_history = pd.concat([df_history, new_row], ignore_index=True)
                df_history.to_csv(HISTORY_FILE, index=False)

                live = True
            except:
                live = False
                mask = (df_history["index"] == index) & (df_history["expiry"] == expiry_type)
                if df_history[mask].empty:
                    st.info("No data yet...")
                    time.sleep(refresh)
                    continue
                row = df_history[mask].iloc[-1]
                price = row["price"]
                ce_lakh = row["ce_oi"]
                pe_lakh = row["pe_oi"]
                net_change = row["net_diff"]

            # Chart Data
            chart_df = df_history[(df_history["index"] == index) & (df_history["expiry"] == expiry_type)].tail(80).copy()
            chart_df["time"] = pd.to_datetime(chart_df["timestamp"]).dt.strftime("%H:%M")

            # Layout
            l, r = st.columns([3.5, 6.5])

            with l:
                st.markdown("#### Open Interest")
                maxv = max(ce_lakh, pe_lakh) * 1.3
                fig_bar = go.Figure()
                fig_bar.add_trace(go.Bar(y=[""], x=[ce_lakh], marker_color="#28a745", text=format_oi(ce_lakh), textposition="outside"))
                fig_bar.add_trace(go.Bar(y=[""], x=[-pe_lakh], marker_color="#e74c3c", text=format_oi(pe_lakh), textposition="outside"))
                fig_bar.update_layout(height=520, barmode="relative", showlegend=False,
                                    xaxis=dict(range=[-maxv, maxv], zeroline=True, zerolinewidth=3),
                                    yaxis_visible=False, margin=dict(t=60))
                st.plotly_chart(fig_bar, use_container_width=True)

                c1, c2 = st.columns(2)
                c1.metric("CE OI", format_oi(ce_lakh))
                c2.metric("PE OI", format_oi(pe_lakh))

            with r:
                st.markdown("#### Change in OI + Net + Price")
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=chart_df["time"], y=chart_df["ce_ch"], name="CE Change", line=dict(color="#28a745", width=4)))
                fig.add_trace(go.Scatter(x=chart_df["time"], y=chart_df["pe_ch"], name="PE Change", line=dict(color="#e74c3c", width=4)))
                fig.add_trace(go.Scatter(x=chart_df["time"], y=chart_df["net_diff"], name="Net CE-PE", line=dict(color="#4361ee", width=5)))
                fig.add_trace(go.Scatter(x=chart_df["time"], y=chart_df["price"], name="Price", yaxis="y2", line=dict(color="#ffc107", width=4, dash="dot")))
                fig.update_layout(height=520, legend=dict(orientation="h", y=1.05), hovermode="x unified",
                                yaxis_title="OI Change (Lakhs)", yaxis2=dict(title="Price", overlaying="y", side="right"))
                st.plotly_chart(fig, use_container_width=True)

            st.success(f"{'LIVE' if live else 'LAST'} • {index} • ₹{price:,.0f} • Net Change: {net_change:+.1f}L")

        # === TAB 2: All Indices Summary ===
        with tab2:
            indices = ["NIFTY", "BANKNIFTY", "FINNIFTY"]
            rows = []
            for sym in indices:
                data = get_oi_data(sym)
                if data:
                    rows.append({
                        "Index": sym,
                        "Price": f"₹{data['price']:,}",
                        "CE OI": format_oi(data['ce_oi']),
                        "PE OI": format_oi(data['pe_oi']),
                        "Net Change": f"{data['net_ch']:+.1f}L",
                        "PCR": data['pcr']
                    })
            if rows:
                summary_df = pd.DataFrame(rows)
                st.dataframe(summary_df.style.highlight_max(axis=0, color='#ffeb3b'), use_container_width=True)
                if refresh_all:
                    st.autorefresh(interval=15000, key="all_refresh")

        st.caption("Made by Amit Bhai • 100% NSE Live • All Data Saved • Works 24x7")

    time.sleep(refresh)
