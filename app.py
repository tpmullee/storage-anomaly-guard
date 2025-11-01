import streamlit as st
import pandas as pd
from src.data_gen import generate_dataset
from src.model import detect_anomalies
from src.app_utils import plot_metric, cache_df, export_anomalies_csv

st.set_page_config(page_title="Storable Edge — Anomaly Guard", layout="wide")

st.title("Storable Edge — Anomaly Guard (Demo)")
st.caption("Seasonality-aware anomaly detection for revenue & payments across facilities")

with st.sidebar:
    st.header("Controls")
    n_fac = st.slider("Number of facilities", 3, 20, 12, step=1)
    days = st.slider("Days of history", 60, 365, 210, step=7)
    seed = st.number_input("Random seed", value=42, step=1)
    metric = st.selectbox("Metric", ["billed_revenue", "payment_success_rate", "move_ins", "delinquencies"])
    facilities = [f"FAC-{i:03d}" for i in range(1, n_fac+1)]
    pick_fac = st.multiselect("Facilities", options=facilities, default=facilities[: min(6, len(facilities))])
    st.markdown("---")
    st.subheader("Model Settings")
    period = st.number_input("STL period (season length)", value=7, step=1)
    if_contam = st.slider("IsolationForest assumed contamination (%%)", 0.1, 10.0, 1.5) / 100.0
    z_thresh = st.slider("|Z| threshold (aux filter)", 1.5, 5.0, 3.0, step=0.1)
    run_btn = st.button("Run detection")

df = cache_df(generate_dataset, days=days, n_facilities=n_fac, seed=seed)
df = df[df["facility"].isin(pick_fac)].reset_index(drop=True)

st.subheader("Sample of data")
st.dataframe(df.head(10), use_container_width=True)

if run_btn:
    with st.spinner("Detecting anomalies..."):
        anomalies, scored = detect_anomalies(df, metric=metric, stl_period=period, iforest_contamination=if_contam, z_abs_threshold=z_thresh)
    st.success(f"""Found {anomalies.shape[0]} anomalies for **{metric}** across {len(pick_fac)} facilities.""")
    st.plotly_chart(plot_metric(scored, metric, anomalies), use_container_width=True)
    st.markdown("### Anomalies")
    st.dataframe(anomalies, use_container_width=True)
    export_anomalies_csv(anomalies)
else:
    st.info("Set options in the sidebar and click **Run detection**.")
