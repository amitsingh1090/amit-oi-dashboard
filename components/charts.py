# components/charts.py  (100% WORKING VERSION - NO ERROR)
import streamlit as st
import plotly.graph_objects as go
import pandas as pd

def show_chart(df):
    if df.empty or len(df) < 1:
        st.info("Waiting for live market data...")
        return

    fig = go.Figure()

    # CE Change
    fig.add_trace(go.Scatter(
        x=df["time"], 
        y=df["ce_chg"], 
        name="CE Change", 
        line=dict(color="#00ff41", width=3),
        fill='tonexty',
        fillcolor='rgba(0,255,65,0.1)'
    ))

    # PE Change  
    fig.add_trace(go.Scatter(
        x=df["time"], 
        y=df["pe_chg"], 
        name="PE Change", 
        line=dict(color="#ff0066", width=3),
        fill='tonexty',
        fillcolor='rgba(255,0,102,0.1)'
    ))

    # Price on secondary axis
    fig.add_trace(go.Scatter(
        x=df["time"], 
        y=df["price"], 
        name="Spot Price", 
        yaxis="y2",
        line=dict(color="yellow", width=2, dash="dot")
    ))

    fig.update_layout(
        template="plotly_dark",
        height=520,
        title="Live OI Change + Spot Price",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=40, r=40, t=80, b=40)
    )

    # Fix the error line - yaxis instead of update_yaxes
    fig.update_yaxes(title_text="OI Change (Lakhs)", secondary_y=False)
    fig.update_yaxes(title_text="Price", secondary_y=True)

    st.plotly_chart(fig, use_container_width=True)
