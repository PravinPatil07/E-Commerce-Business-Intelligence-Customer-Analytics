
# ================================================================
# PHASE 5: RFM CUSTOMER SEGMENTATION
# E-Commerce Business Intelligence & Customer Analytics
# ================================================================
# R = Recency    (How recently customer purchased)
# F = Frequency  (Number of distinct purchases/orders)
# M = Monetary   (Total customer spending/revenue)
#
# Outputs:
# 1. customer_rfm.csv
# 2. rfm_segment_summary.csv
# 3. rfm_segment_distribution.csv
# 4. RFM visualizations
# 5. rfm_business_report.txt
# ================================================================

from pathlib import Path
import warnings

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

warnings.filterwarnings("ignore")

# ---------------- CONFIGURATION ----------------

ROOT = Path(r"D:\E-Commerce Business Intelligence & Customer Analytics")

INPUT_FILE = ROOT / "data" / "processed" / "customer_eligible_sales.csv"

OUTPUT_DIR = ROOT / "reports" / "rfm_analysis"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ---------------- HELPER FUNCTIONS ----------------

def print_section(title):
    print("\n" + "=" * 75)
    print(title)
    print("=" * 75)


def find_column(df, possible_names):
    """
    Find a column using case-insensitive matching.
    """
    columns_map = {
        str(col).strip().lower(): col
        for col in df.columns
    }

    for name in possible_names:
        if name.lower() in columns_map:
            return columns_map[name.lower()]

    return None


def score_quantiles(series, reverse=False):
    """
    Assign scores from 1 to 5 using quantiles.
    Handles duplicate values robustly using rank.
    """
    ranked = series.rank(method="first")

    scores = pd.qcut(
        ranked,
        q=5,
        labels=[1, 2, 3, 4, 5]
    ).astype(int)

    if reverse:
        scores = 6 - scores

    return scores


# ---------------- LOAD DATA ----------------

print_section("PHASE 5: RFM CUSTOMER SEGMENTATION")

if not INPUT_FILE.exists():
    raise FileNotFoundError(
        f"\nInput dataset not found:\n{INPUT_FILE}\n\n"
        "Check that Phase 2 created customer_eligible_sales.csv "
        "inside data/processed."
    )

df = pd.read_csv(INPUT_FILE)

print("Input file:", INPUT_FILE)
print("Dataset shape:", df.shape)
print("\nColumns:")
print(df.columns.tolist())

# ---------------- DETECT COLUMNS ----------------

customer_col = find_column(
    df,
    ["CustomerID", "Customer Id", "Customer_ID", "customer_id"]
)

invoice_col = find_column(
    df,
    ["InvoiceNo", "Invoice", "InvoiceNumber", "OrderID", "Order_ID"]
)

date_col = find_column(
    df,
    ["InvoiceDate", "OrderDate", "Date", "TransactionDate"]
)

quantity_col = find_column(
    df,
    ["Quantity", "Qty"]
)

unit_price_col = find_column(
    df,
    ["UnitPrice", "Unit Price", "Price"]
)

revenue_col = find_column(
    df,
    ["Revenue", "TotalRevenue", "Sales", "Total Sales"]
)

# ---------------- VALIDATION ----------------

required_columns = {
    "Customer ID": customer_col,
    "Invoice/Order ID": invoice_col,
    "Transaction date": date_col
}

missing_required = [
    name for name, col in required_columns.items()
    if col is None
]

if missing_required:
    raise ValueError(
        f"Required columns not found: {missing_required}\n"
        f"Available columns: {df.columns.tolist()}"
    )

if revenue_col is None:
    if quantity_col is not None and unit_price_col is not None:
        print("\nRevenue column not found.")
        print("Calculating Revenue = Quantity × UnitPrice")

        df["Revenue"] = (
            pd.to_numeric(df[quantity_col], errors="coerce")
            * pd.to_numeric(df[unit_price_col], errors="coerce")
        )

        revenue_col = "Revenue"

    else:
        raise ValueError(
            "Revenue column missing and Quantity/UnitPrice "
            "columns are unavailable."
        )

# ---------------- DATA CLEANING ----------------

print_section("DATA PREPARATION")

df[customer_col] = pd.to_numeric(
    df[customer_col],
    errors="coerce"
)

df[date_col] = pd.to_datetime(
    df[date_col],
    errors="coerce"
)

df[revenue_col] = pd.to_numeric(
    df[revenue_col],
    errors="coerce"
)

df[invoice_col] = df[invoice_col].astype(str).str.strip()

# Remove records with missing critical fields
df = df.dropna(
    subset=[
        customer_col,
        invoice_col,
        date_col,
        revenue_col
    ]
)

# Exclude invalid customer IDs
df = df[df[customer_col] > 0]

# Remove invalid invoices
df = df[
    df[invoice_col].notna()
    & (df[invoice_col] != "")
    & (df[invoice_col] != "nan")
]

# Remove negative/zero revenue transactions
df = df[df[revenue_col] > 0]

print("Rows after cleaning:", len(df))
print("Unique customers:", df[customer_col].nunique())
print("Unique orders:", df[invoice_col].nunique())

# ---------------- CALCULATE RFM ----------------

print_section("CALCULATING RFM METRICS")

# Reference date: one day after the most recent transaction
reference_date = df[date_col].max() + pd.Timedelta(days=1)

rfm = df.groupby(customer_col).agg(
    LastPurchaseDate=(date_col, "max"),
    Frequency=(invoice_col, "nunique"),
    Monetary=(revenue_col, "sum")
).reset_index()

rfm.rename(
    columns={customer_col: "CustomerID"},
    inplace=True
)

rfm["Recency"] = (
    reference_date - rfm["LastPurchaseDate"]
).dt.days

rfm["Monetary"] = rfm["Monetary"].round(2)

rfm = rfm[
    [
        "CustomerID",
        "LastPurchaseDate",
        "Recency",
        "Frequency",
        "Monetary"
    ]
].copy()

print("Reference date:", reference_date.date())
print("Customers analyzed:", len(rfm))

# ---------------- RFM SCORES ----------------

print_section("ASSIGNING RFM SCORES")

# Recency: lower days = better score
rfm["R_Score"] = score_quantiles(
    rfm["Recency"],
    reverse=True
)

# Frequency: higher orders = better score
rfm["F_Score"] = score_quantiles(
    rfm["Frequency"]
)

# Monetary: higher revenue = better score
rfm["M_Score"] = score_quantiles(
    rfm["Monetary"]
)

rfm["RFM_Score"] = (
    rfm["R_Score"].astype(str)
    + rfm["F_Score"].astype(str)
    + rfm["M_Score"].astype(str)
)

rfm["RFM_Total_Score"] = (
    rfm["R_Score"]
    + rfm["F_Score"]
    + rfm["M_Score"]
)

# ---------------- SEGMENTATION ----------------

print_section("CUSTOMER SEGMENTATION")

def segment_customer(row):

    R = row["R_Score"]
    F = row["F_Score"]
    M = row["M_Score"]

    # Priority segments
    if R >= 4 and F >= 4 and M >= 4:
        return "Champions"

    elif R >= 3 and F >= 4:
        return "Loyal Customers"

    elif R >= 4 and F >= 2 and M >= 2:
        return "Potential Loyalists"

    elif R >= 4 and F <= 2:
        return "Recent Customers"

    elif R <= 2 and F >= 4 and M >= 4:
        return "Cannot Lose Them"

    elif R <= 2 and F >= 3:
        return "At Risk Customers"

    elif R <= 2 and F <= 2 and M <= 2:
        return "Hibernating Customers"

    elif F <= 2 and M >= 4:
        return "Big Spenders"

    elif R == 3 and F <= 2:
        return "Need Attention"

    else:
        return "Regular Customers"


rfm["CustomerSegment"] = rfm.apply(
    segment_customer,
    axis=1
)

# ---------------- SEGMENT SUMMARY ----------------

print_section("RFM SEGMENT SUMMARY")

segment_summary = rfm.groupby(
    "CustomerSegment"
).agg(
    Customers=("CustomerID", "count"),
    TotalRevenue=("Monetary", "sum"),
    AverageRevenue=("Monetary", "mean"),
    AverageRecency=("Recency", "mean"),
    AverageFrequency=("Frequency", "mean"),
    MedianFrequency=("Frequency", "median"),
    AverageRFMScore=("RFM_Total_Score", "mean")
).reset_index()

segment_summary["CustomerPercentage"] = (
    segment_summary["Customers"]
    / segment_summary["Customers"].sum()
    * 100
)

segment_summary["RevenuePercentage"] = (
    segment_summary["TotalRevenue"]
    / segment_summary["TotalRevenue"].sum()
    * 100
)

segment_summary = segment_summary.sort_values(
    "TotalRevenue",
    ascending=False
)

# Round presentation values
numeric_cols = [
    "TotalRevenue",
    "AverageRevenue",
    "AverageRecency",
    "AverageFrequency",
    "AverageRFMScore",
    "CustomerPercentage",
    "RevenuePercentage"
]

segment_summary[numeric_cols] = (
    segment_summary[numeric_cols].round(2)
)

print(segment_summary.to_string(index=False))

# ---------------- DISTRIBUTION ----------------

segment_distribution = rfm.groupby(
    "CustomerSegment"
).agg(
    CustomerCount=("CustomerID", "count")
).reset_index()

segment_distribution["Percentage"] = (
    segment_distribution["CustomerCount"]
    / segment_distribution["CustomerCount"].sum()
    * 100
)

segment_distribution = segment_distribution.sort_values(
    "CustomerCount",
    ascending=False
)

segment_distribution["Percentage"] = (
    segment_distribution["Percentage"].round(2)
)

# ---------------- EXPORT CSV FILES ----------------

print_section("EXPORTING RESULTS")

rfm_file = OUTPUT_DIR / "customer_rfm.csv"

summary_file = OUTPUT_DIR / "rfm_segment_summary.csv"

distribution_file = OUTPUT_DIR / "rfm_segment_distribution.csv"

rfm.to_csv(
    rfm_file,
    index=False
)

segment_summary.to_csv(
    summary_file,
    index=False
)

segment_distribution.to_csv(
    distribution_file,
    index=False
)

print("Saved:", rfm_file)
print("Saved:", summary_file)
print("Saved:", distribution_file)

# ---------------- VISUALIZATION 1 ----------------

print_section("GENERATING VISUALIZATIONS")

plt.figure(figsize=(10, 6))

score_columns = [
    "R_Score",
    "F_Score",
    "M_Score"
]

for col in score_columns:
    score_counts = rfm[col].value_counts().sort_index()

    plt.plot(
        score_counts.index,
        score_counts.values,
        marker="o",
        label=col
    )

plt.title("RFM Score Distribution")
plt.xlabel("Score (1 to 5)")
plt.ylabel("Number of Customers")
plt.xticks([1, 2, 3, 4, 5])
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()

plt.savefig(
    OUTPUT_DIR / "rfm_scores_distribution.png",
    dpi=300
)

plt.show()

# ---------------- VISUALIZATION 2 ----------------

revenue_plot = segment_summary.sort_values(
    "TotalRevenue",
    ascending=True
)

plt.figure(figsize=(12, 7))

plt.barh(
    revenue_plot["CustomerSegment"],
    revenue_plot["TotalRevenue"]
)

plt.title("Revenue by Customer Segment")
plt.xlabel("Total Revenue")
plt.ylabel("Customer Segment")
plt.tight_layout()

plt.savefig(
    OUTPUT_DIR / "rfm_segment_revenue.png",
    dpi=300
)

plt.show()

# ---------------- VISUALIZATION 3 ----------------

customer_plot = segment_distribution.sort_values(
    "CustomerCount",
    ascending=True
)

plt.figure(figsize=(12, 7))

plt.barh(
    customer_plot["CustomerSegment"],
    customer_plot["CustomerCount"]
)

plt.title("Customer Distribution by RFM Segment")
plt.xlabel("Number of Customers")
plt.ylabel("Customer Segment")
plt.tight_layout()

plt.savefig(
    OUTPUT_DIR / "rfm_segment_customers.png",
    dpi=300
)

plt.show()

# ---------------- BUSINESS REPORT ----------------

print_section("GENERATING BUSINESS REPORT")

total_customers = len(rfm)
total_revenue = rfm["Monetary"].sum()
avg_customer_revenue = rfm["Monetary"].mean()

champions = segment_summary[
    segment_summary["CustomerSegment"] == "Champions"
]

at_risk = segment_summary[
    segment_summary["CustomerSegment"] == "At Risk Customers"
]

hibernating = segment_summary[
    segment_summary["CustomerSegment"] == "Hibernating Customers"
]

cannot_lose = segment_summary[
    segment_summary["CustomerSegment"] == "Cannot Lose Them"
]

report_lines = []

report_lines.append("=" * 70)
report_lines.append("RFM CUSTOMER SEGMENTATION BUSINESS REPORT")
report_lines.append("=" * 70)

report_lines.append(f"Reference Date: {reference_date.date()}")
report_lines.append(f"Total Customers: {total_customers:,}")
report_lines.append(f"Total Customer Revenue: {total_revenue:,.2f}")
report_lines.append(f"Average Revenue per Customer: {avg_customer_revenue:,.2f}")

report_lines.append("\nCUSTOMER SEGMENT SUMMARY")
report_lines.append("-" * 70)

for _, row in segment_summary.iterrows():

    report_lines.append(
        f"{row['CustomerSegment']}: "
        f"{int(row['Customers']):,} customers | "
        f"Revenue: {row['TotalRevenue']:,.2f} | "
        f"Customer share: {row['CustomerPercentage']:.2f}% | "
        f"Revenue share: {row['RevenuePercentage']:.2f}%"
    )

report_lines.append("\nBUSINESS RECOMMENDATIONS")
report_lines.append("-" * 70)

report_lines.append(
    "1. Champions: Reward high-value customers with loyalty benefits "
    "and exclusive offers."
)

report_lines.append(
    "2. Loyal Customers: Encourage repeat purchases using loyalty programs "
    "and personalized recommendations."
)

report_lines.append(
    "3. Potential Loyalists: Encourage additional purchases through "
    "bundles and relevant product recommendations."
)

report_lines.append(
    "4. At Risk Customers: Use targeted re-engagement campaigns "
    "and personalized offers."
)

report_lines.append(
    "5. Cannot Lose Them: Prioritize retention outreach because these "
    "customers previously generated strong revenue."
)

report_lines.append(
    "6. Hibernating Customers: Test low-cost win-back campaigns "
    "before investing heavily in reactivation."
)

report_lines.append(
    "7. Big Spenders: Offer premium products and personalized "
    "recommendations."
)

report_lines.append(
    "8. Recent Customers: Improve the onboarding and second-purchase "
    "experience."
)

report_lines.append("\n" + "=" * 70)

report_text = "\n".join(report_lines)

report_file = OUTPUT_DIR / "rfm_business_report.txt"

with open(
    report_file,
    "w",
    encoding="utf-8"
) as f:

    f.write(report_text)

print(report_text)

# ---------------- FINAL OUTPUT ----------------

print_section("PHASE 5 COMPLETED SUCCESSFULLY")

print("Output directory:")
print(OUTPUT_DIR)

print("\nGenerated files:")

for file in sorted(OUTPUT_DIR.iterdir()):
    print("-", file.name)

print("\nPhase 5 RFM Customer Segmentation is complete.")
print("Review the CSV outputs, visualizations, and business report.")
