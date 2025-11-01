# app.py
import streamlit as st

st.set_page_config(page_title="Storage Anomaly Guard — Home", layout="wide")

with st.sidebar:
    st.markdown("### Storage Anomaly Guard")
    st.page_link("pages/1_👷_Operator_Console.py", label="👷 Operator Console")
    st.page_link("pages/2_👔_Executive_Dashboard.py", label="👔 Executive Dashboard")
    st.page_link("pages/3_🧪_Model_Lab.py", label="🧪 Model Lab")

st.markdown(
    "<h1 style='margin-bottom:0'>Storage Anomaly Guard</h1>"
    "<p style='color:#9aa4b2;margin-top:4px'>Persona-first anomaly detection demo for storage operations</p>",
    unsafe_allow_html=True,
)

st.markdown("### What it is")
st.write(
    "Storage Anomaly Guard automatically spots unusual changes in key business signals—"
    "Billed Revenue, Payment Success Rate, Move-ins, and Delinquencies—across many facilities. "
    "It understands seasonality and recent patterns, then highlights what truly looks off."
)

st.markdown("### Why it’s valuable for storage companies")
st.write(
    "Operators get early warning on revenue leaks and operational hiccups. Alerts are explained in plain language "
    "and prioritized by impact and confidence, so teams can acknowledge, create tasks, and resolve issues quickly."
)

st.markdown("### Why it’s valuable for a SaaS provider")
st.write(
    "Providing proactive detection builds trust and stickiness, reduces support load, and surfaces product insights. "
    "It’s lightweight to run, easy to demo, and improves outcomes for every customer in the portfolio."
)

st.caption("Use the left navigation to open the Operator Console, Executive Dashboard, or Model Lab.")
