"""
Churn model: predicts which customers will NOT buy in the next 90 days.

Training uses many historical cutoff dates. Evaluation uses the most recent cutoff
as a holdout, so the model is always tested on the future relative to its training data.
"""
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score

from ml.features import customer_features, training_cutoffs

HORIZON_DAYS = 90
FEATURES = [
    "recency_days",
    "tenure_days",
    "frequency",
    "monetary",
    "avg_order_value",
    "unique_products",
    "avg_gap_days",
    "spend_last_90",
    "spend_prev_90",
    "spend_change",
]


def build_training_set(df: pd.DataFrame) -> pd.DataFrame:
    frames = []
    for cutoff in training_cutoffs(df, HORIZON_DAYS):
        f = customer_features(df, cutoff, HORIZON_DAYS)
        if not f.empty:
            f["cutoff"] = cutoff
            frames.append(f)
    return pd.concat(frames)


def precision_at_top(y_true, scores, pct: float = 0.10) -> float:
    """Of the riskiest `pct` of customers, what share actually churned?"""
    k = max(1, int(len(scores) * pct))
    top = np.argsort(-np.asarray(scores))[:k]
    return float(np.asarray(y_true)[top].mean())


def new_model():
    return HistGradientBoostingClassifier(
        max_iter=200, learning_rate=0.05, max_depth=4, random_state=42
    )


def train(df: pd.DataFrame):
    """Returns (model fitted on all data, evaluation metrics from a time-based holdout)."""
    data = build_training_set(df)
    last_cutoff = data["cutoff"].max()
    train_d = data[data["cutoff"] < last_cutoff]
    test_d = data[data["cutoff"] == last_cutoff]

    model = new_model()
    model.fit(train_d[FEATURES], train_d["churned"])
    scores = model.predict_proba(test_d[FEATURES])[:, 1]

    y = test_d["churned"].to_numpy()
    metrics = {
        "train_rows": len(train_d),
        "test_rows": len(test_d),
        "base_churn_rate": float(y.mean()),
        "roc_auc": float(roc_auc_score(y, scores)) if 0 < y.sum() < len(y) else np.nan,
        "precision_top10pct": precision_at_top(y, scores),
    }

    # Refit on everything for production scoring
    model.fit(data[FEATURES], data["churned"])
    return model, metrics


def _reasons(r) -> str:
    out = []
    if r["recency_days"] > HORIZON_DAYS:
        out.append(f"No purchase in {int(r['recency_days'])} days")
    if pd.notna(r["avg_gap_days"]) and r["recency_days"] > 2 * r["avg_gap_days"]:
        out.append("Overdue vs usual buying gap")
    if pd.notna(r["spend_change"]) and r["spend_change"] < -0.4:
        out.append(f"Spend down {abs(r['spend_change']) * 100:.0f}% vs prior 90 days")
    if r["frequency"] == 1:
        out.append("Only one order so far")
    return "; ".join(out) or "Stable buying pattern"


def score_current(df: pd.DataFrame, model) -> pd.DataFrame:
    """Score every customer as of the latest date in the data."""
    cutoff = df["InvoiceDate"].max()
    f = customer_features(df, cutoff, HORIZON_DAYS).drop(columns="churned")
    f["churn_probability"] = model.predict_proba(f[FEATURES])[:, 1]
    f["reasons"] = f.apply(_reasons, axis=1)
    out = f.reset_index().rename(columns={"CustomerID": "customer_id"})
    return out.sort_values("churn_probability", ascending=False).reset_index(drop=True)
