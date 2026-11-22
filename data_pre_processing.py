# ================================================================
# PHASE 2: DATA CLEANING & DATA QUALITY ASSESSMENT
# PROJECT: E-Commerce Business Intelligence & Customer Analytics
# ================================================================
# Outputs:
#   data/processed/cleaned_sales.csv
#   data/processed/cancelled_transactions.csv
#   data/processed/customer_eligible_sales.csv
#   reports/data_quality_report.csv
#   reports/missing_values_report.csv
#   reports/duplicate_report.csv
#   reports/invalid_records_report.csv
#   reports/outlier_report.csv
#   reports/phase2_summary.json
# ================================================================

from pathlib import Path
import pandas as pd
import numpy as np
import json
import warnings
from IPython.display import display

warnings.filterwarnings("ignore")

# -------------------- 1. PROJECT CONFIGURATION --------------------

PROJECT_ROOT = Path.cwd()

RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
REPORT_DIR = PROJECT_ROOT / "reports"

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)

print("=" * 80)
print("PHASE 2: DATA CLEANING & DATA QUALITY ASSESSMENT")
print("=" * 80)

print(f"\nProject directory: {PROJECT_ROOT}")
print(f"Raw data folder:  {RAW_DIR}")
print(f"Processed folder:  {PROCESSED_DIR}")
print(f"Reports folder:    {REPORT_DIR}")

# -------------------- 2. FIND DATASET --------------------

if not RAW_DIR.exists():
    raise FileNotFoundError(
        f"\nRaw data folder not found:\n{RAW_DIR}\n"
        "Create data/raw and place your dataset inside it."
    )

supported_files = (
    list(RAW_DIR.glob("*.csv"))
    + list(RAW_DIR.glob("*.xlsx"))
    + list(RAW_DIR.glob("*.xls"))
)

if not supported_files:
    raise FileNotFoundError(
        f"\nNo CSV or Excel dataset found in:\n{RAW_DIR}\n"
        "Place the Online Retail dataset in data/raw."
    )

# Prefer the Online Retail dataset when multiple files exist
preferred_files = [
    f for f in supported_files
    if "retail" in f.name.lower() or "online" in f.name.lower()
]

DATA_FILE = preferred_files[0] if preferred_files else supported_files[0]

print(f"\nSelected dataset: {DATA_FILE.name}")

# -------------------- 3. LOAD DATA --------------------

def load_dataset(file_path):
    suffix = file_path.suffix.lower()

    if suffix == ".csv":
        try:
            return pd.read_csv(file_path, encoding="utf-8")
        except UnicodeDecodeError:
            return pd.read_csv(file_path, encoding="latin1")

    elif suffix in [".xlsx", ".xls"]:
        return pd.read_excel(file_path)

    raise ValueError(f"Unsupported file format: {suffix}")


df_raw = load_dataset(DATA_FILE)

print("\nDataset loaded successfully.")
print(f"Rows:    {df_raw.shape[0]:,}")
print(f"Columns: {df_raw.shape[1]:,}")

print("\nOriginal column names:")
print(df_raw.columns.tolist())

print("\nFirst 5 rows:")
display(df_raw.head())

# -------------------- 4. STANDARDIZE COLUMN NAMES --------------------

df = df_raw.copy()

df.columns = (
    df.columns.astype(str)
    .str.strip()
    .str.replace(r"\s+", "", regex=True)
)

# Standardize known Online Retail column naming
column_mapping = {
    "InvoiceNo": "InvoiceNo",
    "StockCode": "StockCode",
    "Description": "Description",
    "Quantity": "Quantity",
    "InvoiceDate": "InvoiceDate",
    "UnitPrice": "UnitPrice",
    "CustomerID": "CustomerID",
    "Country": "Country"
}

df = df.rename(columns=column_mapping)

required_columns = [
    "InvoiceNo",
    "StockCode",
    "Description",
    "Quantity",
    "InvoiceDate",
    "UnitPrice",
    "CustomerID",
    "Country"
]

missing_columns = [
    col for col in required_columns
    if col not in df.columns
]

if missing_columns:
    raise ValueError(
        f"Required columns missing from dataset: {missing_columns}\n"
        f"Available columns: {df.columns.tolist()}"
    )

# Keep only the columns required for this project
df = df[required_columns].copy()

# -------------------- 5. INITIAL DATA QUALITY REPORT --------------------

initial_rows = len(df)

initial_quality_report = pd.DataFrame({
    "Column": df.columns,
    "Data_Type": [str(df[col].dtype) for col in df.columns],
    "Missing_Count": [df[col].isna().sum() for col in df.columns],
    "Missing_Percentage": [
        round(df[col].isna().mean() * 100, 2)
        for col in df.columns
    ],
    "Unique_Values": [df[col].nunique(dropna=True) for col in df.columns]
})

print("\n" + "=" * 80)
print("INITIAL DATA QUALITY REPORT")
print("=" * 80)

display(initial_quality_report)

# -------------------- 6. MISSING VALUE REPORT --------------------

missing_report = pd.DataFrame({
    "Column": df.columns,
    "Missing_Count": [df[col].isna().sum() for col in df.columns],
    "Missing_Percentage": [
        round(df[col].isna().mean() * 100, 2)
        for col in df.columns
    ]
})

missing_report = missing_report.sort_values(
    by="Missing_Percentage",
    ascending=False
)

print("\nMISSING VALUE ANALYSIS")
display(missing_report)

# -------------------- 7. DATA TYPE CONVERSION --------------------

# Transaction identifiers: keep as strings
df["InvoiceNo"] = df["InvoiceNo"].astype("string").str.strip()
df["StockCode"] = df["StockCode"].astype("string").str.strip()

# Descriptions
df["Description"] = (
    df["Description"]
    .astype("string")
    .str.strip()
)

# Country
df["Country"] = (
    df["Country"]
    .astype("string")
    .str.strip()
)

# Numeric conversion
df["Quantity"] = pd.to_numeric(
    df["Quantity"],
    errors="coerce"
)

df["UnitPrice"] = pd.to_numeric(
    df["UnitPrice"],
    errors="coerce"
)

# Customer ID may contain missing values
df["CustomerID"] = pd.to_numeric(
    df["CustomerID"],
    errors="coerce"
)

# Parse dates
df["InvoiceDate"] = pd.to_datetime(
    df["InvoiceDate"],
    errors="coerce",
    dayfirst=True
)

print("\nDATA TYPES AFTER CONVERSION")
display(pd.DataFrame({
    "Column": df.columns,
    "Data_Type": [str(df[col].dtype) for col in df.columns]
}))

# -------------------- 8. TEXT STANDARDIZATION --------------------

df["Description"] = (
    df["Description"]
    .str.replace(r"\s+", " ", regex=True)
    .str.strip()
)

df["Country"] = (
    df["Country"]
    .str.replace(r"\s+", " ", regex=True)
    .str.strip()
)

# Convert blank text values to missing values
df["Description"] = df["Description"].replace("", pd.NA)
df["Country"] = df["Country"].replace("", pd.NA)
df["StockCode"] = df["StockCode"].replace("", pd.NA)
df["InvoiceNo"] = df["InvoiceNo"].replace("", pd.NA)

# -------------------- 9. DUPLICATE ANALYSIS --------------------

exact_duplicate_mask = df.duplicated(keep="first")

exact_duplicate_count = int(exact_duplicate_mask.sum())

df_deduplicated = df.drop_duplicates(keep="first").copy()

# Additional invoice-line duplicate investigation
invoice_line_keys = [
    "InvoiceNo",
    "StockCode",
    "Quantity",
    "InvoiceDate",
    "UnitPrice"
]

invoice_line_duplicate_count = int(
    df_deduplicated.duplicated(
        subset=invoice_line_keys,
        keep=False
    ).sum()
)

duplicate_report = pd.DataFrame({
    "Duplicate_Type": [
        "Exact duplicate rows",
        "Potential duplicate invoice lines"
    ],
    "Count": [
        exact_duplicate_count,
        invoice_line_duplicate_count
    ],
    "Treatment": [
        "Remove exact duplicate records",
        "Investigate; not automatically removed"
    ]
})

print("\nDUPLICATE ANALYSIS")
display(duplicate_report)

# -------------------- 10. TRANSACTION CLASSIFICATION --------------------

# Cancellation invoices in Online Retail commonly begin with C
cancellation_mask = (
    df_deduplicated["InvoiceNo"]
    .str.upper()
    .str.startswith("C", na=False)
)

cancelled_transactions = df_deduplicated[
    cancellation_mask
].copy()

non_cancelled_transactions = df_deduplicated[
    ~cancellation_mask
].copy()

print("\nTRANSACTION CLASSIFICATION")
print(f"Cancellation rows:     {len(cancelled_transactions):,}")
print(f"Non-cancellation rows: {len(non_cancelled_transactions):,}")

# -------------------- 11. INVALID RECORD ANALYSIS --------------------

invalid_date_mask = (
    non_cancelled_transactions["InvoiceDate"].isna()
)

invalid_quantity_mask = (
    non_cancelled_transactions["Quantity"].isna()
    | (non_cancelled_transactions["Quantity"] <= 0)
)

invalid_price_mask = (
    non_cancelled_transactions["UnitPrice"].isna()
    | (non_cancelled_transactions["UnitPrice"] <= 0)
)

missing_invoice_mask = (
    non_cancelled_transactions["InvoiceNo"].isna()
)

missing_stockcode_mask = (
    non_cancelled_transactions["StockCode"].isna()
)

missing_description_mask = (
    non_cancelled_transactions["Description"].isna()
)

invalid_records_report = pd.DataFrame({
    "Issue": [
        "Missing/invalid invoice number",
        "Missing/invalid transaction date",
        "Missing or non-positive quantity",
        "Missing or non-positive unit price",
        "Missing StockCode",
        "Missing Description",
        "Missing CustomerID"
    ],
    "Count": [
        missing_invoice_mask.sum(),
        invalid_date_mask.sum(),
        invalid_quantity_mask.sum(),
        invalid_price_mask.sum(),
        missing_stockcode_mask.sum(),
        missing_description_mask.sum(),
        non_cancelled_transactions["CustomerID"].isna().sum()
    ]
})

print("\nINVALID RECORD ANALYSIS")
display(invalid_records_report)

# -------------------- 12. CLEANING FILTERS --------------------

# Keep valid completed-sale records
valid_sales_mask = (
    ~invalid_date_mask
    & ~invalid_quantity_mask
    & ~invalid_price_mask
    & ~missing_invoice_mask
    & ~missing_stockcode_mask
    & ~missing_description_mask
)

cleaned_sales = non_cancelled_transactions[
    valid_sales_mask
].copy()

# -------------------- 13. FEATURE ENGINEERING --------------------

cleaned_sales["Revenue"] = (
    cleaned_sales["Quantity"]
    * cleaned_sales["UnitPrice"]
)

cleaned_sales["InvoiceYear"] = (
    cleaned_sales["InvoiceDate"].dt.year
)

cleaned_sales["InvoiceMonth"] = (
    cleaned_sales["InvoiceDate"].dt.month
)

cleaned_sales["InvoiceYearMonth"] = (
    cleaned_sales["InvoiceDate"].dt.to_period("M").astype(str)
)

cleaned_sales["InvoiceQuarter"] = (
    cleaned_sales["InvoiceDate"].dt.quarter
)

cleaned_sales["InvoiceDay"] = (
    cleaned_sales["InvoiceDate"].dt.day
)

cleaned_sales["InvoiceDayOfWeek"] = (
    cleaned_sales["InvoiceDate"].dt.dayofweek
)

cleaned_sales["InvoiceDayName"] = (
    cleaned_sales["InvoiceDate"].dt.day_name()
)

cleaned_sales["InvoiceHour"] = (
    cleaned_sales["InvoiceDate"].dt.hour
)

cleaned_sales["IsWeekend"] = (
    cleaned_sales["InvoiceDate"].dt.dayofweek >= 5
)

cleaned_sales["CustomerID"] = (
    cleaned_sales["CustomerID"].astype("Int64")
)

# -------------------- 14. CUSTOMER-ELIGIBLE DATASET --------------------

# Customer analytics require an identifiable CustomerID
customer_eligible_sales = cleaned_sales[
    cleaned_sales["CustomerID"].notna()
].copy()

# -------------------- 15. OUTLIER ANALYSIS --------------------

def calculate_iqr_outliers(series):
    series = series.dropna()

    if len(series) == 0:
        return {
            "Q1": np.nan,
            "Q3": np.nan,
            "IQR": np.nan,
            "Lower_Bound": np.nan,
            "Upper_Bound": np.nan,
            "Outlier_Count": 0,
            "Outlier_Percentage": 0
        }

    q1 = series.quantile(0.25)
    q3 = series.quantile(0.75)
    iqr = q3 - q1

    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr

    outliers = (
        (series < lower_bound)
        | (series > upper_bound)
    )

    return {
        "Q1": round(float(q1), 4),
        "Q3": round(float(q3), 4),
        "IQR": round(float(iqr), 4),
        "Lower_Bound": round(float(lower_bound), 4),
        "Upper_Bound": round(float(upper_bound), 4),
        "Outlier_Count": int(outliers.sum()),
        "Outlier_Percentage": round(
            float(outliers.mean() * 100), 2
        )
    }


quantity_outliers = calculate_iqr_outliers(
    cleaned_sales["Quantity"]
)

price_outliers = calculate_iqr_outliers(
    cleaned_sales["UnitPrice"]
)

revenue_outliers = calculate_iqr_outliers(
    cleaned_sales["Revenue"]
)

outlier_report = pd.DataFrame([
    {"Metric": "Quantity", **quantity_outliers},
    {"Metric": "UnitPrice", **price_outliers},
    {"Metric": "Revenue", **revenue_outliers}
])

print("\nOUTLIER ANALYSIS")
display(outlier_report)

# We are NOT deleting outliers automatically.
# High-value orders can be legitimate business transactions.

# -------------------- 16. DATA QUALITY SUMMARY --------------------

final_rows = len(cleaned_sales)

cleaning_summary = {
    "project": "E-Commerce Business Intelligence & Customer Analytics",
    "phase": "Phase 2 - Data Cleaning & Data Quality Assessment",
    "source_file": DATA_FILE.name,
    "initial_rows": int(initial_rows),
    "initial_columns": int(df_raw.shape[1]),
    "exact_duplicates_removed": int(exact_duplicate_count),
    "cancellation_rows": int(len(cancelled_transactions)),
    "non_cancellation_rows": int(len(non_cancelled_transactions)),
    "cleaned_sales_rows": int(final_rows),
    "customer_eligible_rows": int(len(customer_eligible_sales)),
    "rows_removed_from_non_cancellation_sales": int(
        len(non_cancelled_transactions) - final_rows
    ),
    "unique_invoices": int(cleaned_sales["InvoiceNo"].nunique()),
    "unique_products": int(cleaned_sales["StockCode"].nunique()),
    "unique_customers": int(
        cleaned_sales["CustomerID"].nunique()
    ),
    "total_quantity": int(cleaned_sales["Quantity"].sum()),
    "total_revenue": round(
        float(cleaned_sales["Revenue"].sum()), 2
    ),
    "date_min": (
        cleaned_sales["InvoiceDate"].min().strftime("%Y-%m-%d")
        if final_rows else None
    ),
    "date_max": (
        cleaned_sales["InvoiceDate"].max().strftime("%Y-%m-%d")
        if final_rows else None
    ),
    "missing_customer_id_in_cleaned_sales": int(
        cleaned_sales["CustomerID"].isna().sum()
    ),
    "customer_id_coverage_percentage": round(
        customer_eligible_sales.shape[0] / final_rows * 100, 2
    ) if final_rows else 0
}

# -------------------- 17. EXPORT REPORTS --------------------

initial_quality_report.to_csv(
    REPORT_DIR / "data_quality_report.csv",
    index=False
)

missing_report.to_csv(
    REPORT_DIR / "missing_values_report.csv",
    index=False
)

duplicate_report.to_csv(
    REPORT_DIR / "duplicate_report.csv",
    index=False
)

invalid_records_report.to_csv(
    REPORT_DIR / "invalid_records_report.csv",
    index=False
)

outlier_report.to_csv(
    REPORT_DIR / "outlier_report.csv",
    index=False
)

with open(
    REPORT_DIR / "phase2_summary.json",
    "w",
    encoding="utf-8"
) as f:
    json.dump(
        cleaning_summary,
        f,
        indent=4,
        ensure_ascii=False
    )

# -------------------- 18. EXPORT CLEANED DATA --------------------

cleaned_sales.to_csv(
    PROCESSED_DIR / "cleaned_sales.csv",
    index=False
)

cancelled_transactions.to_csv(
    PROCESSED_DIR / "cancelled_transactions.csv",
    index=False
)

customer_eligible_sales.to_csv(
    PROCESSED_DIR / "customer_eligible_sales.csv",
    index=False
)

# Optional Parquet export
try:
    cleaned_sales.to_parquet(
        PROCESSED_DIR / "cleaned_sales.parquet",
        index=False
    )
    print("\nParquet export successful.")
except Exception as e:
    print(f"\nParquet export skipped: {e}")

# -------------------- 19. FINAL VALIDATION --------------------

assert cleaned_sales["InvoiceDate"].notna().all()
assert (cleaned_sales["Quantity"] > 0).all()
assert (cleaned_sales["UnitPrice"] > 0).all()
assert cleaned_sales["InvoiceNo"].notna().all()
assert cleaned_sales["StockCode"].notna().all()
assert cleaned_sales["Description"].notna().all()
assert cleaned_sales["Revenue"].notna().all()
assert (cleaned_sales["Revenue"] > 0).all()

# Ensure cancellation invoices are excluded
assert not cleaned_sales["InvoiceNo"].str.upper().str.startswith(
    "C", na=False
).any()

# Customer analytics dataset must contain CustomerID
assert customer_eligible_sales["CustomerID"].notna().all()

print("\nAll validation checks passed.")

# -------------------- 20. FINAL SUMMARY --------------------

print("\n" + "=" * 80)
print("PHASE 2 COMPLETED - DATA CLEANING SUMMARY")
print("=" * 80)

summary_table = pd.DataFrame({
    "Metric": [
        "Original rows",
        "Original columns",
        "Exact duplicate rows removed",
        "Cancellation records",
        "Completed valid sales records",
        "Customer-eligible records",
        "Unique invoices",
        "Unique products",
        "Unique customers",
        "Total units sold",
        "Total revenue",
        "Customer ID coverage",
        "Start date",
        "End date"
    ],
    "Value": [
        f"{cleaning_summary['initial_rows']:,}",
        f"{cleaning_summary['initial_columns']:,}",
        f"{cleaning_summary['exact_duplicates_removed']:,}",
        f"{cleaning_summary['cancellation_rows']:,}",
        f"{cleaning_summary['cleaned_sales_rows']:,}",
        f"{cleaning_summary['customer_eligible_rows']:,}",
        f"{cleaning_summary['unique_invoices']:,}",
        f"{cleaning_summary['unique_products']:,}",
        f"{cleaning_summary['unique_customers']:,}",
        f"{cleaning_summary['total_quantity']:,}",
        f"{cleaning_summary['total_revenue']:,.2f}",
        f"{cleaning_summary['customer_id_coverage_percentage']}%",
        cleaning_summary["date_min"],
        cleaning_summary["date_max"]
    ]
})

display(summary_table)

print("\nOUTPUT FILES")
print("-" * 80)

for file_path in sorted(PROCESSED_DIR.glob("*")):
    print(f"Processed: {file_path.name}")

for file_path in sorted(REPORT_DIR.glob("*")):
    print(f"Report:    {file_path.name}")

print("\nPHASE 2 SUCCESSFULLY COMPLETED.")
print("Next step: Phase 3 - Exploratory Data Analysis (EDA)")