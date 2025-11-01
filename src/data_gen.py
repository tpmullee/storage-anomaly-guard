# src/data_gen.py
from __future__ import annotations
import numpy as np
import pandas as pd

def _seasonal_pattern(n, period=7, amplitude=1.0):
    x = np.arange(n)
    return amplitude * (np.sin(2*np.pi * x/period) + 0.3*np.cos(2*np.pi * x/period))

def generate_dataset(days: int = 210, n_facilities: int = 12, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    end_date = pd.Timestamp.today().normalize()
    return _gen_range(end_date=end_date, days=days, n_facilities=n_facilities, rng=rng)

def extend_dataset(df: pd.DataFrame, days: int = 30, seed: int | None = None) -> pd.DataFrame:
    """Continue the series by <days> using same facilities & behavior."""
    if df.empty:
        return df
    rng = np.random.default_rng(seed)
    end_date = pd.to_datetime(df["date"]).max()
    return pd.concat(
        [df, _gen_range(end_date=end_date + pd.Timedelta(days=days), days=days,
                        n_facilities=df["facility"].nunique(), rng=rng,
                        facility_ids=sorted(df["facility"].unique()))],
        ignore_index=True
    )

def _gen_range(end_date: pd.Timestamp, days: int, n_facilities: int, rng, facility_ids: list[str] | None = None):
    dates = pd.date_range(end=end_date, periods=days, freq="D")
    rows = []
    for f in range(n_facilities):
        facility = facility_ids[f] if facility_ids else f"FAC-{f+1:03d}"
        rev_base = rng.uniform(6000, 18000)
        payrate_base = rng.uniform(0.86, 0.97)
        moveins_base = rng.integers(1, 7)
        delin_base = rng.uniform(0.02, 0.08)

        season = _seasonal_pattern(days, period=7, amplitude=rng.uniform(0.2, 0.5))

        billed_rev = (rev_base * (1 + 0.08*season) + rng.normal(0, rev_base*0.03, size=days)).clip(1000, None)
        pay_success = (payrate_base + 0.03*season + rng.normal(0, 0.01, size=days)).clip(0.5, 1.0)
        move_ins = (moveins_base + 2*season + rng.normal(0, 1.0, size=days)).round().clip(0, None)
        delinq = (delin_base - 0.01*season + rng.normal(0, 0.003, size=days)).clip(0.0, 0.3)

        # Inject a few anomalies per facility
        idxs = rng.choice(np.arange(days), size=rng.integers(2, 6), replace=False)
        for i in idxs:
            billed_rev[i] *= rng.uniform(0.5, 1.7)
            pay_success[i] += rng.uniform(-0.15, 0.15)
            move_ins[i] += rng.integers(-4, 6)
            delinq[i] += rng.uniform(-0.04, 0.08)

        rows.append(pd.DataFrame({
            "date": dates.date,
            "facility": facility,
            "billed_revenue": billed_rev,
            "payment_success_rate": pay_success,
            "move_ins": move_ins,
            "delinquencies": delinq,
        }))
    return pd.concat(rows, ignore_index=True)
