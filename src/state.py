# src/state.py
from __future__ import annotations
import streamlit as st
import pandas as pd
from typing import Tuple
from .data_gen import generate_dataset, extend_dataset
from .model import detect_anomalies

DEFAULTS = dict(
    days=210, n_facilities=12, seed=42,
    stl_period=7, iforest_contamination=0.015, z_abs_threshold=3.0,
    metric="billed_revenue"
)

def ensure_state():
    if "df" not in st.session_state:
        st.session_state.df = generate_dataset(
            days=DEFAULTS["days"], n_facilities=DEFAULTS["n_facilities"], seed=DEFAULTS["seed"]
        )
    if "metric" not in st.session_state:
        st.session_state.metric = DEFAULTS["metric"]
    if "params" not in st.session_state:
        st.session_state.params = dict(
            stl_period=DEFAULTS["stl_period"],
            iforest_contamination=DEFAULTS["iforest_contamination"],
            z_abs_threshold=DEFAULTS["z_abs_threshold"],
        )
    if "last_run" not in st.session_state:
        st.session_state.last_run = None
    if "anomalies" not in st.session_state:
        st.session_state.anomalies = pd.DataFrame()
    if "notifications" not in st.session_state:
        st.session_state.notifications = []
    if "ack" not in st.session_state:
        st.session_state.ack = set()

def _alert_id(row: pd.Series) -> str:
    return f"{row['facility']}|{row['metric']}|{row['date']}"

def run_detection(selected_facilities: list[str] | None = None, note_scan: bool = True) -> Tuple[pd.DataFrame, pd.DataFrame]:
    df = st.session_state.df
    if selected_facilities:
        df = df[df["facility"].isin(selected_facilities)].copy()
    out, scored = detect_anomalies(
        df,
        metric=st.session_state.metric,
        stl_period=st.session_state.params["stl_period"],
        iforest_contamination=st.session_state.params["iforest_contamination"],
        z_abs_threshold=st.session_state.params["z_abs_threshold"],
    )
    st.session_state.last_run = {"facilities": selected_facilities or "ALL"}
    st.session_state.anomalies = out

    # Notifications
    if note_scan:
        st.session_state.notifications.append(
            f"Scan complete: {out.shape[0]} {st.session_state.metric.replace('_',' ').title()} alerts found."
        )
    return out, scored

def advance_one_month(seed: int | None = None):
    st.session_state.df = extend_dataset(st.session_state.df, days=30, seed=seed)
