# components/charts.py  → FINAL ZERO-ERROR VERSION
import streamlit as st
import plotly.graph_objects as go

def show_chart(df):
    if df.empty or len(df) == 0:
        st.info("Market closed hai ya data aa raha hai... kal 9:15 se live hoga")
        return

    fig = go.Figure()

    # CE OI Change
    fig.add_trace(go.Scatter(x=df['time'], y=df['ce_chg'],
                             mode='lines+markers',
                             name='CE Change',
                             line=dict(color='#00ff41', width=4)))

    # PE OI Change
    fig.add_trace(go.Scatter(x=df['time'], y=df['pe_chg'],
                             mode='lines+markers',
                             name='PE Change',
                             line=dict(color='#ff0066', width=4)))

    # Price on right axis
    fig.add_trace(go.Scatter(x=df['time'], y=df['price'],
                             mode='lines',
                             name='Spot Price',
                             yaxis='y2',
                             line=dict(color='yellow', width=2, dash='dot')))

    fig.update_layout(
        template="plotly_dark",
        height=550,
        title="Live OI Change + Price Movement",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        yaxis=dict(title="OI Change (Lakhs)"),
        yaxis2=dict(title="Price", overlaying="y", side="right")
    )

    st.plotly_chart(fig, use_container_width=True)
