# pages/2_👔_Executive_Dashboard.py
import streamlit as st
import pandas as pd
import plotly.express as px
from src.state import ensure_state, run_detection
from src.ux import top_bar, friendly_metric, us_date, section_box, render_sidebar_nav

st.set_page_config(page_title="Storage Anomaly Guard — Executive Dashboard", layout="wide")
ensure_state()
render_sidebar_nav()

notif_count = len(st.session_state.notifications)
top_bar("Executive Dashboard", alerts_count=notif_count)

# Filters (boxed)
with section_box("Filters"):
    c1, c2 = st.columns([0.4, 0.6])
    facilities_all = sorted(st.session_state.df["facility"].unique())
    with c1:
        metric = st.selectbox("Portfolio Metric", ["billed_revenue", "payment_success_rate", "move_ins", "delinquencies"])
        if metric != st.session_state.metric:
            st.session_state.metric = metric
    with c2:
        pick_fac = st.multiselect("Portfolio Scope", facilities_all, default=facilities_all)

out, scored = run_detection(selected_facilities=pick_fac)
df = scored.copy()
df["date"] = pd.to_datetime(df["date"])
latest = df["date"].max()

# Overview (boxed)
with section_box("Overview"):
    alerts_30d = out[out["date"] >= (latest - pd.Timedelta(days=30)).date()]
    fac_ct = df["facility"].nunique()
    anom_rate = 0 if df.empty else (len(out) / len(df)) * 100
    est_savings = max(0, alerts_30d.shape[0] * 250)  # demo heuristic
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Facilities", fac_ct)
    k2.metric("30-day Alerts", int(len(alerts_30d)))
    k3.metric("Anomaly Rate", f"{anom_rate:.2f}%")
    k4.metric("Value Protected (30d)", f"${est_savings:,.0f}")

# Trend (boxed)
with section_box(f"{friendly_metric(st.session_state.metric)} — Portfolio Trend"):
    fig = px.line(df, x="date", y=st.session_state.metric, color="facility",
                  title=None)
    fig.update_layout(xaxis_title="Date", yaxis_title=friendly_metric(st.session_state.metric))
    st.plotly_chart(fig, use_container_width=True)

# Distribution + high priority (boxed)
with section_box("Alerts by Facility (last 90 days)"):
    recent = out[out["date"] >= (latest - pd.Timedelta(days=90)).date()]
    if recent.empty:
        st.info("No recent alerts.")
    else:
        counts = recent.groupby("facility").size().reset_index(name="alerts")
        bar = px.bar(counts, x="facility", y="alerts", title=None)
        st.plotly_chart(bar, use_container_width=True)

        csv = recent.copy()
        csv["date"] = csv["date"].apply(us_date)
        st.download_button("Download Monthly Alert Report (CSV)", csv.to_csv(index=False).encode("utf-8"),
                           "monthly_alerts.csv", "text/csv")

with section_box("High-Priority (last 90 days)"):
    hp = recent[recent["priority"] == "High"].sort_values("date", ascending=False).head(12) if not recent.empty else pd.DataFrame()
    if hp.empty:
        st.info("No high-priority alerts in the last 90 days.")
    else:
        hp_disp = hp[["date","facility","metric","priority","confidence"]].copy()
        hp_disp["date"] = hp_disp["date"].apply(us_date)
        hp_disp["metric"] = hp_disp["metric"].apply(friendly_metric)
        st.dataframe(hp_disp, use_container_width=True)
