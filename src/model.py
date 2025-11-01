# src/model.py
from __future__ import annotations
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from statsmodels.tsa.seasonal import STL

FRIENDLY = {
    "billed_revenue": "Billed Revenue",
    "payment_success_rate": "Payment Success Rate",
    "move_ins": "Move-ins",
    "delinquencies": "Delinquencies",
}

def _stl_residuals(y: np.ndarray, period: int = 7) -> np.ndarray:
    s = pd.Series(y.astype(float))
    stl = STL(s, period=period, robust=True)
    res = stl.fit()
    return (s - res.trend - res.seasonal).values

def _rolling_zscore(x: np.ndarray, window: int = 14) -> np.ndarray:
    s = pd.Series(x)
    m = s.rolling(window, min_periods=5).mean()
    v = s.rolling(window, min_periods=5).std()
    z = (s - m) / (v.replace(0, np.nan))
    return z.fillna(0.0).values

def _mad(values: np.ndarray) -> float:
    med = np.median(values)
    return float(np.median(np.abs(values - med)))

def _priority_and_confidence(abs_z: float, resid: float, resid_mad: float, iso_decision: float,
                             dec_min: float, dec_max: float) -> tuple[str, float, float]:
    resid_scale = 0.0
    if resid_mad and resid_mad > 0:
        resid_scale = min(abs(resid) / (3 * resid_mad), 1.0)

    z_scale = min(abs_z / 4.0, 1.0)
    score = 0.6 * z_scale + 0.4 * resid_scale

    if dec_max - dec_min <= 1e-9:
        conf = 0.5
    else:
        conf = 1.0 - ((iso_decision - dec_min) / (dec_max - dec_min))
    conf = float(np.clip(conf, 0.0, 1.0))

    if score >= 0.75:
        pr = "High"
    elif score >= 0.45:
        pr = "Medium"
    else:
        pr = "Low"
    return pr, float(score), conf

def detect_anomalies(
    df: pd.DataFrame,
    metric: str,
    stl_period: int = 7,
    iforest_contamination: float = 0.015,
    z_abs_threshold: float = 3.0,
):
    assert metric in FRIENDLY

    out_rows, scored_frames = [], []

    for fac, sub in df.sort_values("date").groupby("facility"):
        y = sub[metric].values.astype(float)
        resid = _stl_residuals(y, period=stl_period)
        rz = _rolling_zscore(resid, window=14)
        lvl_rz = _rolling_zscore(sub[metric].values.astype(float), window=14)

        X = np.c_[resid, rz, lvl_rz]
        iforest = IsolationForest(n_estimators=200, contamination=iforest_contamination, random_state=42)
        pred = iforest.fit_predict(X)
        iso_decision = iforest.decision_function(X)
        dec_min, dec_max = float(iso_decision.min()), float(iso_decision.max())

        aux_flag = (np.abs(rz) >= z_abs_threshold).astype(int)
        labels = ((-pred + 1) // 2)
        labels = ((labels > 0) | (aux_flag > 0)).astype(int)

        sub_scored = sub.copy()
        sub_scored[f"{metric}_residual"] = resid
        sub_scored["rolling_z"] = rz
        sub_scored["level_rolling_z"] = lvl_rz
        sub_scored["iso_decision"] = iso_decision
        sub_scored["anomaly_label"] = labels

        # Baselines (last 14 days) for friendlier “why”
        s_metric = pd.Series(sub[metric].values.astype(float))
        base_mean = s_metric.rolling(14, min_periods=7).mean().fillna(method="bfill").values
        base_median = s_metric.rolling(14, min_periods=7).median().fillna(method="bfill").values

        resid_mad = _mad(resid) if len(resid) else 0.0
        p_list, s_list, c_list, why_list = [], [], [], []
        for i, (az, r, d, val) in enumerate(zip(np.abs(rz), resid, iso_decision, s_metric.values)):
            pr, ps, cf = _priority_and_confidence(az, r, resid_mad, d, dec_min, dec_max)
            p_list.append(pr); s_list.append(ps); c_list.append(cf)
            bm, bmed = base_mean[i], base_median[i]
            diff = val - bmed
            why = (
                f"Unusual vs recent pattern (|Z|={az:.2f}). "
                f"Median≈{bmed:,.2f}, Avg≈{bm:,.2f}, Diff≈{diff:+,.2f}. Residual={r:.1f}."
            )
            why_list.append(why)

        sub_scored["priority"] = p_list
        sub_scored["priority_score"] = s_list
        sub_scored["confidence"] = c_list
        sub_scored["why_text"] = why_list

        scored_frames.append(sub_scored)

        if labels.any():
            anomalies = sub_scored.loc[labels == 1, ["date", "facility", metric,
                                                     f"{metric}_residual", "rolling_z",
                                                     "iso_decision", "priority", "priority_score",
                                                     "confidence", "why_text"]].copy()
            anomalies["metric"] = metric
            out_rows.append(anomalies)

    scored = pd.concat(scored_frames, ignore_index=True) if scored_frames else df.copy()
    out = pd.concat(out_rows, ignore_index=True) if out_rows else pd.DataFrame(columns=[
        "date","facility",metric,f"{metric}_residual","rolling_z","iso_decision","priority",
        "priority_score","confidence","why_text","metric"
    ])
    out = out.sort_values(["date","facility"]).reset_index(drop=True)
    return out, scored
