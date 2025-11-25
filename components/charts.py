# components/charts.py
import streamlit as st
import plotly.graph_objects as go
import pandas as pd

def show_chart(df):
    if df.empty:
        st.info("Waiting for live data...")
        return
        
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["time"], y=df["ce_chg"], name="CE Change", 
                             line=dict(color="#00ff41", width=3), fill='tonexty'))
    fig.add_trace(go.Scatter(x=df["time"], y=df["pe_chg"], name="PE Change", 
                             line=dict(color="#ff0066", width=3), fill='tonexty'))
    fig.add_trace(go.Scatter(x=df["time"], y=df["price"], name="Spot Price", 
                             yaxis="y2", line=dict(color="yellow", dash="dot")))
    fig.update_layout(template="plotly_dark", height=500, title="Live OI Change + Price")
    fig.update_yaxes(title_text="OI Change (Lakhs)", secondary_y=False)
    fig.update_yaxes(title_text="Price", secondary_y=True)
    st.plotly_chart(fig, use_container_width=True)
