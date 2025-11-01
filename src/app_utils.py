# src/app_utils.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

@st.cache_data(show_spinner=False)
def cache_df(_fn, **kwargs):  # underscore = do not hash callable
    return _fn(**kwargs)

def plot_metric(scored: pd.DataFrame, metric: str, anomalies: pd.DataFrame):
    fig = go.Figure()
    for fac, sub in scored.groupby("facility"):
        fig.add_trace(go.Scatter(x=sub["date"], y=sub[metric], mode="lines", name=f"{fac}"))
    if not anomalies.empty:
        fig.add_trace(go.Scatter(
            x=anomalies["date"], y=anomalies[metric], mode="markers", name="anomaly",
            marker=dict(size=10, symbol="x")))
    fig.update_layout(
        title=f"{metric} with flagged anomalies",
        xaxis_title="Date", yaxis_title=metric, legend_title="Facility")
    return fig

def export_anomalies_csv(anomalies: pd.DataFrame):
    if anomalies.empty:
        st.info("No anomalies to export.")
        return
    csv = anomalies.to_csv(index=False).encode("utf-8")
    st.download_button("Download anomalies CSV", csv, file_name="anomalies.csv", mime="text/csv")
