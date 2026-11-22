"""
Analytics layer. Every KPI shown on the dashboard is calculated here with pandas.
The Flask routes in app.py only call these functions and render the results.
"""
import sqlite3
from contextlib import closing
from functools import lru_cache

import numpy as np
import pandas as pd

from config import Config

WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# Segment label -> (short description, chart colour). Labels match your RFM CSV output.
SEGMENT_META = {
    "Champions": ("Bought recently, buy often, spend the most.", "#16a34a"),
    "Loyal Customers": ("Buy regularly and spend well. Upsell premium products.", "#22c55e"),
    "Potential Loyalists": ("Recent with decent frequency. Nurture them.", "#84cc16"),
    "Recent Customers": ("Bought most recently but not often yet. Build the habit.", "#06b6d4"),
    "Regular Customers": ("Steady, mid-level activity across all metrics.", "#3b82f6"),
    "Big Spenders": ("High spend, low frequency. Target with high-value offers.", "#8b5cf6"),
    "Need Attention": ("Above-average past activity, slipping recently. Re-engage.", "#eab308"),
    "At Risk Customers": ("Used to buy often but have not returned lately.", "#f97316"),
    "Cannot Lose Them": ("High frequency and spend, but long inactive. Win back urgently.", "#ef4444"),
    "Hibernating Customers": ("Low recency, frequency and spend. Long inactive.", "#6b7280"),
}
DEFAULT_META = ("", "#94a3b8")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def safe_div(numerator, denominator):
    """Divide, returning None instead of raising or returning inf."""
    if denominator is None or pd.isna(denominator) or denominator == 0:
        return None
    return float(numerator) / float(denominator)


def _py(value):
    """Convert numpy scalars to plain Python so Jinja/tojson can handle them."""
    return value.item() if isinstance(value, np.generic) else value


def to_records(df):
    """DataFrame -> list of dicts with NaN/NA/inf replaced by None."""
    df = df.replace([np.inf, -np.inf], np.nan)
    df = df.astype(object).where(df.notna(), None)
    return [{k: _py(v) for k, v in row.items()} for row in df.to_dict(orient="records")]


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------
@lru_cache(maxsize=1)
def load_sales() -> pd.DataFrame:
    """Load the sales table once and add the derived time columns."""
    if not Config.DB_PATH.exists():
        raise FileNotFoundError(
            f"Database not found at {Config.DB_PATH}. Set the ECOM_DB_PATH environment variable."
        )

    with closing(sqlite3.connect(Config.DB_PATH)) as conn:
        df = pd.read_sql_query(f"SELECT * FROM {Config.SALES_TABLE}", conn)

    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"], errors="coerce")
    df = df.dropna(subset=["InvoiceDate"]).copy()

    df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce")
    df["UnitPrice"] = pd.to_numeric(df["UnitPrice"], errors="coerce")
    df["CustomerID"] = pd.to_numeric(df["CustomerID"], errors="coerce").astype("Int64")

    if "Revenue" not in df.columns or df["Revenue"].isna().all():
        df["Revenue"] = df["Quantity"] * df["UnitPrice"]
    df["Revenue"] = pd.to_numeric(df["Revenue"], errors="coerce")

    df["Year"] = df["InvoiceDate"].dt.year
    df["Month"] = df["InvoiceDate"].dt.month
    df["YearMonth"] = df["InvoiceDate"].dt.to_period("M").astype(str)
    df["Weekday"] = df["InvoiceDate"].dt.day_name()
    df["Hour"] = df["InvoiceDate"].dt.hour
    return df


def get_years():
    return sorted(int(y) for y in load_sales()["Year"].unique())


def filter_sales(year=None) -> pd.DataFrame:
    df = load_sales()
    if year is not None:
        df = df[df["Year"] == year]
    return df


# ---------------------------------------------------------------------------
# Overview KPIs
# ---------------------------------------------------------------------------
def overview_kpis(df: pd.DataFrame) -> dict:
    revenue = float(df["Revenue"].sum())
    orders = int(df["InvoiceNo"].nunique())
    customers = int(df["CustomerID"].nunique())          # unique non-null CustomerID
    units = float(df["Quantity"].sum())

    return {
        "total_revenue": revenue,
        "total_orders": orders,
        "total_customers": customers,
        "aov": safe_div(revenue, orders),                     # Revenue ÷ orders
        "total_units": units,
        "revenue_per_customer": safe_div(revenue, customers), # Revenue ÷ customers
        "asp": safe_div(revenue, units),                      # Revenue ÷ quantity
        "orders_per_customer": safe_div(orders, customers),   # Orders ÷ customers
    }


# ---------------------------------------------------------------------------
# Sales analytics
# ---------------------------------------------------------------------------
def monthly_sales(df: pd.DataFrame) -> pd.DataFrame:
    g = (
        df.groupby("YearMonth")
        .agg(
            revenue=("Revenue", "sum"),
            orders=("InvoiceNo", "nunique"),
            customers=("CustomerID", "nunique"),
        )
        .reset_index()
    )
    g["aov"] = g["revenue"] / g["orders"]
    g["revenue_growth"] = g["revenue"].pct_change() * 100   # Month-over-Month revenue growth %
    g["order_growth"] = g["orders"].pct_change() * 100      # Month-over-Month order growth %
    return g


def sales_by_weekday(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby("Weekday").agg(revenue=("Revenue", "sum"), orders=("InvoiceNo", "nunique"))
    return g.reindex(WEEKDAYS, fill_value=0).rename_axis("weekday").reset_index()


def sales_by_hour(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby("Hour").agg(revenue=("Revenue", "sum"), orders=("InvoiceNo", "nunique"))
    return g.reindex(range(24), fill_value=0).rename_axis("hour").reset_index()


def revenue_year_month_matrix(df: pd.DataFrame) -> dict:
    pv = df.pivot_table(index="Year", columns="Month", values="Revenue", aggfunc="sum")
    pv = pv.reindex(columns=range(1, 13))
    values = [[None if pd.isna(v) else float(v) for v in row] for row in pv.to_numpy()]
    flat = [v for row in values for v in row if v is not None]
    return {
        "years": [int(y) for y in pv.index],
        "months": MONTH_NAMES,
        "rows": values,              # NOTE: not "values" -- clashes with dict.values in Jinja
        "max_value": max(flat) if flat else 0,
    }


# ---------------------------------------------------------------------------
# Product analytics
# ---------------------------------------------------------------------------
def product_table(df: pd.DataFrame) -> pd.DataFrame:
    total_revenue = df["Revenue"].sum()
    g = (
        df.groupby("StockCode")
        .agg(
            description=("Description", "first"),
            revenue=("Revenue", "sum"),
            units=("Quantity", "sum"),
            orders=("InvoiceNo", "nunique"),
            customers=("CustomerID", "nunique"),
        )
        .reset_index()
    )
    g["avg_revenue_per_unit"] = g["revenue"] / g["units"]          # Average Revenue per Unit
    g["revenue_rank"] = g["revenue"].rank(method="min", ascending=False).astype(int)
    g["revenue_contribution"] = g["revenue"] / total_revenue * 100  # Product Revenue Contribution %
    return g.sort_values("revenue", ascending=False)


# ---------------------------------------------------------------------------
# Customer analytics
# ---------------------------------------------------------------------------
def customer_table(df: pd.DataFrame) -> pd.DataFrame:
    c = (
        df.dropna(subset=["CustomerID"])
        .groupby("CustomerID")
        .agg(revenue=("Revenue", "sum"), orders=("InvoiceNo", "nunique"))
        .reset_index()
    )
    c["aov"] = c["revenue"] / c["orders"]
    c["revenue_rank"] = c["revenue"].rank(method="min", ascending=False).astype(int)
    c["customer_type"] = np.where(c["orders"] > 1, "Repeat", "One-Time")
    return c.sort_values("revenue", ascending=False)


def customer_summary(customers: pd.DataFrame) -> dict:
    total = len(customers)
    repeat = int((customers["orders"] > 1).sum())
    one_time = total - repeat
    return {
        "total": total,
        "repeat": repeat,
        "one_time": one_time,
        "repeat_pct": safe_div(repeat * 100, total),
    }


# ---------------------------------------------------------------------------
# RFM analytics (reads the customer-level RFM output)
# ---------------------------------------------------------------------------
@lru_cache(maxsize=1)
def load_rfm() -> pd.DataFrame:
    if not Config.RFM_PATH.exists():
        raise FileNotFoundError(
            f"RFM file not found at {Config.RFM_PATH}. Set the ECOM_RFM_PATH environment variable."
        )
    df = pd.read_csv(Config.RFM_PATH)
    df["CustomerSegment"] = df["CustomerSegment"].str.strip()
    return df


def rfm_summary() -> dict:
    r = load_rfm()
    total_customers = len(r)                       # RFM Customer Count
    total_revenue = float(r["Monetary"].sum())

    g = (
        r.groupby("CustomerSegment")
        .agg(
            customers=("CustomerID", "count"),
            revenue=("Monetary", "sum"),                 # Segment Revenue
            avg_recency=("Recency", "mean"),
            avg_frequency=("Frequency", "mean"),
            avg_monetary=("Monetary", "mean"),
        )
        .reset_index()
    )
    g["customer_pct"] = g["customers"] / total_customers * 100
    g["revenue_pct"] = g["revenue"] / total_revenue * 100   # Segment Revenue Contribution
    g["description"] = g["CustomerSegment"].map(lambda s: SEGMENT_META.get(s, DEFAULT_META)[0])
    g["color"] = g["CustomerSegment"].map(lambda s: SEGMENT_META.get(s, DEFAULT_META)[1])
    g = g.sort_values("revenue", ascending=False)

    return {
        "total_customers": total_customers,
        "total_revenue": total_revenue,
        "segments": to_records(g),
    }
