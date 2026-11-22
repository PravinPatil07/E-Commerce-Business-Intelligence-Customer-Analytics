"""
Feature engineering for forecasting and churn.
Everything is built from the sales DataFrame returned by analytics.load_sales().
"""
import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Monthly time series (for forecasting)
# ---------------------------------------------------------------------------
def monthly_series(df: pd.DataFrame, drop_partial_last_month: bool = True) -> pd.DataFrame:
    """Monthly revenue and orders with a continuous month index (missing months = 0)."""
    m = df.assign(month=df["InvoiceDate"].dt.to_period("M").dt.to_timestamp())
    g = (
        m.groupby("month")
        .agg(revenue=("Revenue", "sum"), orders=("InvoiceNo", "nunique"))
        .sort_index()
    )
    g = g.reindex(pd.date_range(g.index.min(), g.index.max(), freq="MS"), fill_value=0.0)
    g.index.name = "month"

    # The last month is often incomplete (data stops mid-month). Drop it so it
    # doesn't look like a sudden crash in revenue.
    last_date = df["InvoiceDate"].max()
    if (
        drop_partial_last_month
        and g.index[-1] == last_date.to_period("M").to_timestamp()
        and last_date.day < last_date.days_in_month - 2
    ):
        g = g.iloc[:-1]
    return g


# ---------------------------------------------------------------------------
# Customer-level features (for churn)
# ---------------------------------------------------------------------------
def customer_features(df: pd.DataFrame, cutoff, horizon_days: int = 90) -> pd.DataFrame:
    """
    Features for every customer who bought on or before `cutoff`.
    Only data up to `cutoff` is used for features (no leakage).
    `churned` = 1 if the customer made NO purchase in the `horizon_days` after cutoff.
    """
    cutoff = pd.Timestamp(cutoff)
    known = df[df["CustomerID"].notna() & (df["InvoiceDate"] <= cutoff)].copy()
    if known.empty:
        return pd.DataFrame()
    known["CustomerID"] = known["CustomerID"].astype("int64")

    g = known.groupby("CustomerID")
    feats = pd.DataFrame({
        "recency_days": (cutoff - g["InvoiceDate"].max()).dt.days,
        "tenure_days": (cutoff - g["InvoiceDate"].min()).dt.days,
        "frequency": g["InvoiceNo"].nunique(),
        "monetary": g["Revenue"].sum(),
        "unique_products": g["StockCode"].nunique(),
    })
    feats["avg_order_value"] = feats["monetary"] / feats["frequency"]

    # Average days between orders (NaN for customers with a single order)
    orders = (
        known.groupby(["CustomerID", "InvoiceNo"])["InvoiceDate"].min()
        .reset_index()
        .sort_values(["CustomerID", "InvoiceDate"])
    )
    gaps = orders.groupby("CustomerID")["InvoiceDate"].diff().dt.days
    feats["avg_gap_days"] = gaps.groupby(orders["CustomerID"]).mean()

    # Spending trend: last 90 days vs the 90 days before that
    recent_start = cutoff - pd.Timedelta(days=90)
    prev_start = cutoff - pd.Timedelta(days=180)
    last = known[known["InvoiceDate"] > recent_start].groupby("CustomerID")["Revenue"].sum()
    prev = known[
        (known["InvoiceDate"] > prev_start) & (known["InvoiceDate"] <= recent_start)
    ].groupby("CustomerID")["Revenue"].sum()
    feats["spend_last_90"] = last.reindex(feats.index).fillna(0.0)
    feats["spend_prev_90"] = prev.reindex(feats.index).fillna(0.0)
    feats["spend_change"] = (
        (feats["spend_last_90"] - feats["spend_prev_90"])
        / feats["spend_prev_90"].replace(0, np.nan)
    )

    # Label: did the customer buy in the horizon after cutoff?
    future = df[
        df["CustomerID"].notna()
        & (df["InvoiceDate"] > cutoff)
        & (df["InvoiceDate"] <= cutoff + pd.Timedelta(days=horizon_days))
    ]
    buyers = list(future["CustomerID"].astype("int64").unique())
    feats["churned"] = (~feats.index.isin(buyers)).astype(int)
    return feats


def training_cutoffs(df: pd.DataFrame, horizon_days: int = 90, min_history_days: int = 180):
    """Monthly cutoff dates, leaving enough history before and enough future after."""
    start = (df["InvoiceDate"].min() + pd.Timedelta(days=min_history_days)).normalize()
    end = (df["InvoiceDate"].max() - pd.Timedelta(days=horizon_days)).normalize()
    return pd.date_range(start, end, freq="MS")
