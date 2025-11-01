# Storage Anomaly Guard (Demo)

A persona-first, seasonality-aware anomaly detection demo tailored for a Storage FMS.

- **Operator Console** – alert cards, one-line explanations, acknowledge, and “Create Task” (full-screen modal)
- **Executive Dashboard** – portfolio KPIs, trends, distribution, CSV export
- **Model Lab** – knobs for STL + IsolationForest, with results preview

## Why this demo works

- **Use-case:** Mature, ERP-like systems struggle to surface subtle revenue/payment anomalies across many facilities. This app proactively flags them and explains **why** in human terms.
- **Model:** STL decomposition (trend + weekly seasonality) + IsolationForest on residual features. It’s robust, fast, and easy to reason about for non-ML stakeholders.
- **UX:** Clear page titles, boxed sections, compact alert cards, one-line explanations, and a focused full-screen **Task** modal (clean attention switch).

## Quickstart

> Python 3.10–3.12 recommended

```bash
# 1) Create and activate venv
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 2) Install dependencies
pip install -r requirements.txt

# 3) Run
streamlit run app.py
```
Open the URL that Streamlit prints. Use the **Operator Console** to explore alerts, or **Executive Dashboard** for portfolio-level views. **Model Lab** is for tuning.

## Repo Layout

```
.
├── app.py
├── pages/
│   ├── 1_👷_Operator_Console.py
│   ├── 2_👔_Executive_Dashboard.py
│   └── 3_🧪_Model_Lab.py
├── src/
│   ├── app_utils.py
│   ├── data_gen.py
│   ├── model.py
│   ├── state.py
│   └── ux.py
├── requirements.txt
└── README.md
```

## Tech Notes

- **STL + Residuals**: weekly seasonality (period=7) with robust trend, residual outliers are candidate anomalies.
- **IsolationForest**: contamination controls overall sensitivity; we also use a rolling-z sanity gate.
- **One-line “Why”**: “$X above expected; a large signal from Anomaly Guard.” Classifies strength by |z|.
- **Demo controls**: Always available in the sidebar and on the landing page.

## Extend

- Wire “Create Task” to a real API (CRM/CMMS).
- Push alerts to Slack/email/webhooks.
- Add feedback loop for threshold tuning.
