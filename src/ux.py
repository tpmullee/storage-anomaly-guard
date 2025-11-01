# src/ux.py
from __future__ import annotations
import streamlit as st
import pandas as pd
import plotly.express as px
from contextlib import contextmanager

FRIENDLY = {
    "billed_revenue": "Billed Revenue",
    "payment_success_rate": "Payment Success Rate",
    "move_ins": "Move-ins",
    "delinquencies": "Delinquencies",
}

px.defaults.template = "plotly_dark"

def us_date(value) -> str:
    d = pd.to_datetime(value)
    return d.strftime("%m/%d/%Y")

def friendly_metric(metric_key: str) -> str:
    return FRIENDLY.get(metric_key, metric_key.replace("_", " ").title())

def fmt_money(v: float) -> str:
    return f"${v:,.2f}"

def fmt_percent(v: float) -> str:
    return f"{v*100:.0f}%" if abs(v) <= 1.2 else f"{v:.0f}%"

def operator_why_sentence(row: pd.Series, metric_key: str) -> str:
    resid = float(row.get(f"{metric_key}_residual", 0.0))
    z = abs(float(row.get("rolling_z", 0.0)))
    if metric_key == "billed_revenue":
        amt = fmt_money(abs(resid))
    elif metric_key in ("payment_success_rate", "delinquencies"):
        amt = fmt_percent(abs(resid))
    else:
        amt = f"{abs(resid):,.0f}"
    direction = "above" if resid >= 0 else "below"
    size = "critical" if z >= 4 else "large" if z >= 3 else "moderate" if z >= 2 else "minor"
    return f"{amt} {direction} expected; a {size} signal from Anomaly Guard."

def _inject_css():
    st.markdown(
        """
        <style>
        section[data-testid="stSidebarNav"] { display: none !important; }
        .topbar { margin-bottom: .25rem; }
        .badge { display:inline-block; padding:.1rem .45rem; border-radius:9999px; font-size:.70rem; }
        .badge-high { background:#ef4444; color:white; }
        .badge-med  { background:#f59e0b; color:black; }
        .badge-low  { background:#10b981; color:black; }
        .alert-card { padding: .9rem 1rem; border-radius: 12px; border: 1px solid #1f2937; background:#0f172a; }
        .alert-title { font-weight:700; font-size:1rem; margin:0 0 .25rem 0; }
        .meta { color:#cbd5e1; font-size:.9rem; }
        .value { font-size:1.6rem; font-weight:700; margin:.25rem 0 .5rem; }
        .section-box { background:#0f172a; border:1px solid #1f2937; border-radius:12px; padding:1rem 1.25rem; margin:.75rem 0 1rem; }
        .section-title { font-size:1.05rem; font-weight:700; margin:0 0 .75rem 0; }
        .tiny-note { color:#93a2b8; font-size:.85rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )

def priority_badge(level: str) -> str:
    icon = "▲" if level == "High" else ("▸" if level == "Medium" else "•")
    cls = "badge-low"
    if level == "High": cls = "badge-high"
    elif level == "Medium": cls = "badge-med"
    return f"<span class='badge {cls}'>{icon} {level}</span>"

def top_bar(title: str, alerts_count: int = 0):
    _inject_css()
    left, mid, right = st.columns([0.6, 0.2, 0.2], gap="small")
    with left:
        st.markdown(f"<div class='topbar'><h2 style='margin:.25rem 0'>{title}</h2></div>", unsafe_allow_html=True)
    with mid:
        st.empty()
    with right:
        label = f"🔔 Notifications ({alerts_count})" if alerts_count else "🔔 Notifications"
        with st.popover(label, use_container_width=True):
            st.markdown("#### Recent Alerts")
            notes = st.session_state.get("notifications", [])[-15:][::-1]
            if not notes:
                st.caption("No new notifications.")
            else:
                for n in notes:
                    st.write("• ", n)
            if st.button("Clear all"):
                st.session_state.notifications = []

def facilities_selector(options: list[str], default: list[str]) -> list[str]:
    sel = st.session_state.get("fac_sel", default)
    label = f"{len(sel)} facilities selected" if len(sel) > 1 else (sel[0] if sel else "Select facilities")
    with st.popover(label, use_container_width=True):
        chosen = st.multiselect("Choose facilities", options=options, default=sel, key="fac_sel_ms")
        st.caption("Close popover to apply.")
        sel = chosen
    return sel

@contextmanager
def section_box(title: str | None = None):
    _inject_css()
    st.markdown("<div class='section-box'>", unsafe_allow_html=True)
    if title:
        st.markdown(f"<div class='section-title'>{title}</div>", unsafe_allow_html=True)
    try:
        yield
    finally:
        st.markdown("</div>", unsafe_allow_html=True)

def render_sidebar_nav():
    _inject_css()
    with st.sidebar:
        st.markdown("## Storage Anomaly Guard")
        st.caption("Proactive anomaly detection for storage operations.")
        st.markdown("**What it is**")
        st.write(
            "Automatically spots unusual changes in Billed Revenue, Payment Success Rate, "
            "Move-ins, and Delinquencies across facilities—accounting for seasonality and trend."
        )
        st.markdown("**Why storage companies value it**")
        st.write(
            "Early warning on revenue leaks and operational hiccups with plain-language explanations "
            "and prioritized alerts that turn into tasks in seconds."
        )
        st.markdown("**Why a SaaS provider benefits**")
        st.write(
            "Builds trust and stickiness, reduces support load, and surfaces product insights—"
            "while remaining lightweight to demo and deploy."
        )
        st.markdown("---")
        st.page_link("pages/1_👷_Operator_Console.py", label="👷 Operator Console")
        st.page_link("pages/2_👔_Executive_Dashboard.py", label="👔 Executive Dashboard")
        st.page_link("pages/3_🧪_Model_Lab.py", label="🧪 Model Lab")
        st.markdown("---")
        st.caption("Demo only")
        if st.button("▶️ Advance month & scan (demo)", use_container_width=True, key="sb_demo_advance"):
            st.session_state["_sidebar_advance"] = True
        if st.button("🔁 Rescan now (demo)", use_container_width=True, key="sb_demo_rescan"):
            st.session_state["_sidebar_rescan"] = True
