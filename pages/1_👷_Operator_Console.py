# pages/1_👷_Operator_Console.py
import streamlit as st
import pandas as pd
from src.state import ensure_state, run_detection, advance_one_month, _alert_id
from src.ux import (
    top_bar, friendly_metric, us_date, priority_badge,
    facilities_selector, fmt_money, fmt_percent, render_sidebar_nav,
    section_box, operator_why_sentence,
)

# Browser tab title best-practice: App — Page
st.set_page_config(page_title="Storage Anomaly Guard — Operator Console", layout="wide")
ensure_state()
render_sidebar_nav()

# ── Full-screen modal for Task creation (focused action) ──
def open_task_modal(row, display_val):
    st.session_state["task_modal_data"] = {
        "id": _alert_id(row),
        "facility": row["facility"],
        "metric": friendly_metric(row["metric"]),
        "date": us_date(row["date"]),
        "observed": display_val,
        "why": operator_why_sentence(row, row["metric"]),
    }
    st.session_state["task_modal_open"] = True

@st.dialog("New Task", width="large")
def task_modal():
    data = st.session_state.get("task_modal_data", {})
    st.caption("Create an operator task (demo)")
    title = st.text_input(
        "Title",
        value=f"{data.get('metric','')} anomaly at {data.get('facility','')}",
        key=f"title_{data.get('id','')}",
    )
    assignee = st.selectbox(
        "Assignee",
        ["Unassigned", "Onsite Manager", "District Manager", "Accounting"],
        key=f"assignee_{data.get('id','')}",
    )
    due = st.date_input(
        "Due date",
        value=pd.to_datetime(data.get("date","01/01/2025")).date(),
        key=f"due_{data.get('id','')}",
    )
    desc_default = (
        f"Auto-created from anomaly: {data.get('metric','')} on {data.get('date','')} "
        f"at {data.get('facility','')}.\nObserved: {data.get('observed','')}\n{data.get('why','')}"
    )
    st.text_area("Description", value=desc_default, height=160, key=f"desc_{data.get('id','')}")
    cols = st.columns([0.15, 0.85])
    if cols[0].button("Save task", type="primary", key=f"save_{data.get('id','')}"):
        st.toast("Task created.", icon="✅")
        st.session_state["task_modal_open"] = False
        st.rerun()
    cols[1].caption("This is a demo form.")
if st.session_state.get("task_modal_open"):
    task_modal()

# ── Header + Notifications ──
notif_count = len(st.session_state.notifications)
top_bar("Storage Anomaly Guard — Operator Console", alerts_count=notif_count)
st.markdown(
    "_Spot and act on unusual changes in **Billed Revenue**, **Payment Success Rate**, "
    "**Move-ins**, and **Delinquencies**. Alerts are prioritized and explained in plain language._"
)

# “Demo only” controls live in the sidebar (always visible)
with st.sidebar:
    st.markdown("#### Demo controls")
    if st.button("▶️ Advance month & scan (demo)", use_container_width=True):
        advance_one_month(seed=7)
        run_detection(selected_facilities=None, note_scan=True)
        st.toast("Month advanced → new data scanned.", icon="⏭️")
    if st.button("🔁 Rescan now (demo)", use_container_width=True):
        run_detection(selected_facilities=None, note_scan=True)

# ── Filters (boxed section) ──
with section_box("Filters"):
    c1, c2, c3, c4, c5 = st.columns([0.25, 0.22, 0.15, 0.19, 0.19])
    facilities_all = sorted(st.session_state.df["facility"].unique())
    with c1:
        pick_fac = facilities_selector(facilities_all, default=facilities_all[:6])
    with c2:
        metric_labels = {
            "billed_revenue": "Billed Revenue",
            "payment_success_rate": "Payment Success Rate",
            "move_ins": "Move-ins",
            "delinquencies": "Delinquencies",
        }
        rev = {v: k for k, v in metric_labels.items()}
        current_label = metric_labels.get(st.session_state.metric, st.session_state.metric.title())
        chosen_label = st.selectbox(
            "Focus Metric",
            list(metric_labels.values()),
            index=list(metric_labels.values()).index(current_label),
            key="focus_metric_selector",
        )
        metric = rev[chosen_label]
        if metric != st.session_state.metric:
            st.session_state.metric = metric
            st.session_state.ack = set()
            run_detection(selected_facilities=pick_fac, note_scan=False)
    with c3:
        sort_by = st.selectbox("Sort", ["Priority", "Newest", "Confidence"], key="sort_selector")
    with c4:
        date_start = st.date_input("From",
            value=pd.to_datetime(st.session_state.df["date"]).min().date(), key="date_from")
    with c5:
        date_end = st.date_input("To",
            value=pd.to_datetime(st.session_state.df["date"]).max().date(), key="date_to")

# Seed anomalies (no spam)
if st.session_state.anomalies.empty:
    run_detection(selected_facilities=pick_fac, note_scan=False)

# Apply filters
anom = st.session_state.anomalies.copy()
if pick_fac:
    anom = anom[anom["facility"].isin(pick_fac)]
if 'date_start' in locals():
    anom = anom[pd.to_datetime(anom["date"]) >= pd.to_datetime(date_start)]
if 'date_end' in locals():
    anom = anom[pd.to_datetime(anom["date"]) <= pd.to_datetime(date_end)]
# Remove acknowledged
if st.session_state.get("ack"):
    anom["__id"] = anom.apply(_alert_id, axis=1)
    anom = anom[~anom["__id"].isin(st.session_state.ack)]

# Sort
if not anom.empty:
    if sort_by == "Priority":
        pr_map = {"High": 3, "Medium": 2, "Low": 1}
        anom["__prank"] = anom["priority"].map(pr_map)
        anom = anom.sort_values(["__prank", "priority_score"], ascending=[False, False])
    elif sort_by == "Newest":
        anom = anom.sort_values("date", ascending=False)
    else:
        anom = anom.sort_values("confidence", ascending=False)

# ── Overview (boxed section) ──
with section_box("Overview"):
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Facilities in scope", len(sorted(anom["facility"].unique())) if not anom.empty else 0)
    k2.metric("Alerts shown", anom.shape[0])
    k3.metric("High priority", int((anom["priority"] == "High").sum()) if not anom.empty else 0)
    latest_date = pd.to_datetime(st.session_state.df["date"]).max().date()
    k4.metric("Latest data", latest_date.strftime("%m/%d/%Y"))

# ── Alerts (boxed section) ──
with section_box(f"Alerts — {friendly_metric(st.session_state.metric)}"):
    if anom.empty:
        st.success("No alerts in the selected window. ✅")
    else:
        cols = st.columns(3)
        for _, row in anom.head(30).iterrows():
            alert_id = _alert_id(row)
            with cols[list(cols).index(cols[0]) if False else (cols.index(cols[0]) if False else 0)]:  # no-op line to avoid linter noise
                pass
            with cols[(hash(alert_id) % 3)]:  # spread cards a bit more evenly
                with st.container(border=True):
                    t1, t2 = st.columns([0.65, 0.35])
                    with t1:
                        st.markdown(f"**{row['facility']} • {friendly_metric(row['metric'])}**")
                        st.caption(f"Date: {us_date(row['date'])}")
                    with t2:
                        st.markdown(priority_badge(row["priority"]), unsafe_allow_html=True)
                        st.caption(f"Conf. {int(row['confidence']*100)}%")

                    # Observed value with proper units
                    val = row[st.session_state.metric]
                    if st.session_state.metric == "billed_revenue":
                        display_val = fmt_money(val)
                    elif st.session_state.metric in ("payment_success_rate", "delinquencies"):
                        display_val = fmt_percent(val)
                    else:
                        display_val = f"{val:,.0f}"
                    st.markdown(f"### {display_val}")

                    # One-line, operator-friendly reason
                    st.caption(operator_why_sentence(row, st.session_state.metric))

                    # Actions
                    b1, b2, b3 = st.columns([0.28, 0.34, 0.38])
                    if b1.button("Acknowledge", key=f"ack_{alert_id}", use_container_width=True):
                        st.session_state.ack.add(alert_id); st.rerun()
                    if b2.button("Create Task", key=f"task_{alert_id}", use_container_width=True):
                        open_task_modal(row, display_val); st.rerun()
                    b3.button("Assign to Team", key=f"assign_{alert_id}", use_container_width=True)

# Details table
with st.expander("See all alerts (table)"):
    table = anom.copy()
    table["date"] = table["date"].apply(us_date)
    table.rename(columns={
        "facility": "Facility",
        st.session_state.metric: friendly_metric(st.session_state.metric),
        "priority": "Priority",
        "confidence": "Confidence",
    }, inplace=True)
    st.dataframe(table, use_container_width=True)
