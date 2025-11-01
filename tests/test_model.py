import pandas as pd
from src.data_gen import generate_dataset
from src.model import detect_anomalies

def test_detect_runs():
    df = generate_dataset(days=90, n_facilities=3, seed=7)
    out, scored = detect_anomalies(df, metric="billed_revenue", stl_period=7, iforest_contamination=0.05, z_abs_threshold=2.5)
    # Should return frames with expected columns
    assert isinstance(out, pd.DataFrame)
    assert isinstance(scored, pd.DataFrame)
    assert "anomaly_label" in scored.columns
