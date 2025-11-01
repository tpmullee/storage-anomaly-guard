# pages/3_🧪_Model_Lab.py
import streamlit as st
from src.state import ensure_state, run_detection
from src.app_utils import plot_metric, export_anomalies_csv
from src.ux import top_bar, friendly_metric, section_box, render_sidebar_nav  # minimal imports (avoid cycles)

st.set_page_config(page_title="Storage Anomaly Guard — Model Lab", layout="wide")
ensure_state()
render_sidebar_nav()
top_bar("Model Lab", alerts_count=len(st.session_state.notifications))

st.markdown("_For power users: tune, run, and inspect results. (Execs can skip this.)_")

# Parameters (boxed)
with section_box("Parameters"):
    facilities_all = sorted(st.session_state.df["facility"].unique())
    pick_fac = st.multiselect("Facilities", options=facilities_all,
                              default=facilities_all[: min(6, len(facilities_all))])
    metric = st.selectbox("Metric", ["billed_revenue", "payment_success_rate", "move_ins", "delinquencies"])
    if metric != st.session_state.metric:
        st.session_state.metric = metric
    st.session_state.params["stl_period"] = st.number_input(
        "STL period (season length)", value=st.session_state.params["stl_period"], step=1)
    st.session_state.params["iforest_contamination"] = st.slider(
        "IsolationForest contamination (%)", 0.1, 10.0,
        float(st.session_state.params["iforest_contamination"]*100)) / 100.0
    st.session_state.params["z_abs_threshold"] = st.slider(
        "|Z| threshold (aux filter)", 1.0, 5.0, float(st.session_state.params["z_abs_threshold"]), step=0.1)
    run_btn = st.button("Run detection")

# Data sample (boxed)
with section_box("Data sample"):
    st.dataframe(st.session_state.df.head(10), use_container_width=True)

# Results (boxed)
if run_btn:
    anomalies, scored = run_detection(selected_facilities=pick_fac)
    with section_box(f"Results — {friendly_metric(st.session_state.metric)}"):
        st.success(f"Found {anomalies.shape[0]} anomalies.")
        st.plotly_chart(plot_metric(scored, st.session_state.metric, anomalies), use_container_width=True)
        st.markdown("### Anomalies")
        st.dataframe(anomalies, use_container_width=True)
        export_anomalies_csv(anomalies)
else:
    st.info("Set parameters and click **Run detection**.")
