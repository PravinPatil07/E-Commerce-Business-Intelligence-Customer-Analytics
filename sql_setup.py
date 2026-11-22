# =============================================================================
# PHASE 4: SQL DATABASE SETUP
# E-COMMERCE BUSINESS INTELLIGENCE & CUSTOMER ANALYTICS
# =============================================================================
# Creates SQLite database and imports Phase 2 cleaned datasets.
# Compatible with Windows / VS Code / Conda.
# =============================================================================

from pathlib import Path
import sqlite3
import pandas as pd

# ---------------------------- CONFIGURATION ------------------------------------

PROJECT_ROOT = Path.cwd()

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DATABASE_DIR = PROJECT_ROOT / "database"
RESULTS_DIR = PROJECT_ROOT / "reports" / "sql_results"

DATABASE_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

DATABASE_PATH = DATABASE_DIR / "ecommerce_analytics.db"

SALES_FILE = PROCESSED_DIR / "cleaned_sales.csv"
CUSTOMER_FILE = PROCESSED_DIR / "customer_eligible_sales.csv"
CANCELLATION_FILE = PROCESSED_DIR / "cancelled_transactions.csv"

print("=" * 85)
print("PHASE 4 - SQL DATABASE SETUP")
print("=" * 85)

# ---------------------------- VALIDATE FILES ---------------------------------

if not SALES_FILE.exists():
    raise FileNotFoundError(
        f"Cleaned sales file not found:\n{SALES_FILE}\n"
        "Run Phase 2 data cleaning first."
    )

# ---------------------------- LOAD DATA ---------------------------------------

sales = pd.read_csv(SALES_FILE)
sales["InvoiceDate"] = pd.to_datetime(
    sales["InvoiceDate"], errors="coerce"
)

sales["InvoiceNo"] = sales["InvoiceNo"].astype("string")
sales["StockCode"] = sales["StockCode"].astype("string")

# Ensure Revenue is available
if "Revenue" not in sales.columns:
    sales["Revenue"] = sales["Quantity"] * sales["UnitPrice"]

# Customer dataset
if CUSTOMER_FILE.exists():
    customer_sales = pd.read_csv(CUSTOMER_FILE)
else:
    customer_sales = sales[
        sales["CustomerID"].notna()
    ].copy()

# Cancellation dataset
if CANCELLATION_FILE.exists():
    cancellations = pd.read_csv(CANCELLATION_FILE)
else:
    cancellations = pd.DataFrame()

print("\nDataset loading:")
print(f"Sales records: {len(sales):,}")
print(f"Customer-eligible records: {len(customer_sales):,}")
print(f"Cancellation records: {len(cancellations):,}")

# ---------------------------- CONNECT DATABASE -------------------------------

conn = sqlite3.connect(DATABASE_PATH)

# ---------------------------- IMPORT TABLES ----------------------------------

sales.to_sql(
    "sales",
    conn,
    if_exists="replace",
    index=False
)

customer_sales.to_sql(
    "customer_sales",
    conn,
    if_exists="replace",
    index=False
)

if not cancellations.empty:
    cancellations.to_sql(
        "cancellations",
        conn,
        if_exists="replace",
        index=False
    )
else:
    # Create an empty table if there are no cancellation records
    pd.DataFrame(
        columns=sales.columns
    ).to_sql(
        "cancellations",
        conn,
        if_exists="replace",
        index=False
    )

# ---------------------------- CREATE INDEXES ---------------------------------

index_statements = [
    "CREATE INDEX IF NOT EXISTS idx_sales_invoice ON sales(InvoiceNo)",
    "CREATE INDEX IF NOT EXISTS idx_sales_customer ON sales(CustomerID)",
    "CREATE INDEX IF NOT EXISTS idx_sales_product ON sales(StockCode)",
    "CREATE INDEX IF NOT EXISTS idx_sales_date ON sales(InvoiceDate)",
    "CREATE INDEX IF NOT EXISTS idx_customer_customer ON customer_sales(CustomerID)",
    "CREATE INDEX IF NOT EXISTS idx_customer_invoice ON customer_sales(InvoiceNo)",
    "CREATE INDEX IF NOT EXISTS idx_customer_date ON customer_sales(InvoiceDate)"
]

for statement in index_statements:
    conn.execute(statement)

# ---------------------------- CREATE VIEWS ----------------------------------

# Invoice-level sales analysis
conn.execute("""
CREATE VIEW IF NOT EXISTS order_summary AS
SELECT
    InvoiceNo,
    MIN(InvoiceDate) AS OrderDate,
    CustomerID,
    COUNT(DISTINCT StockCode) AS UniqueProducts,
    SUM(Quantity) AS TotalUnits,
    SUM(Revenue) AS OrderRevenue
FROM sales
GROUP BY InvoiceNo, CustomerID
""")

# Customer-level lifetime analysis
conn.execute("""
CREATE VIEW IF NOT EXISTS customer_summary AS
SELECT
    CustomerID,
    COUNT(DISTINCT InvoiceNo) AS TotalOrders,
    SUM(Revenue) AS TotalRevenue,
    SUM(Quantity) AS TotalUnits,
    MIN(InvoiceDate) AS FirstPurchase,
    MAX(InvoiceDate) AS LastPurchase,
    AVG(UnitPrice) AS AverageUnitPrice
FROM customer_sales
GROUP BY CustomerID
""")

conn.commit()

# ---------------------------- VALIDATE DATABASE ------------------------------

print("\nDatabase tables:")

tables = pd.read_sql_query("""
SELECT name
FROM sqlite_master
WHERE type = 'table'
ORDER BY name
""", conn)

print(tables.to_string(index=False))

print("\nDatabase views:")

views = pd.read_sql_query("""
SELECT name
FROM sqlite_master
WHERE type = 'view'
ORDER BY name
""", conn)

print(views.to_string(index=False))

# Row count validation
validation = pd.read_sql_query("""
SELECT
    (SELECT COUNT(*) FROM sales) AS Sales_Rows,
    (SELECT COUNT(*) FROM customer_sales) AS Customer_Sales_Rows,
    (SELECT COUNT(*) FROM cancellations) AS Cancellation_Rows,
    (SELECT COUNT(DISTINCT InvoiceNo) FROM sales) AS Unique_Orders,
    (SELECT COUNT(DISTINCT CustomerID)
     FROM customer_sales) AS Unique_Customers,
    (SELECT COUNT(DISTINCT StockCode)
     FROM sales) AS Unique_Products,
    (SELECT ROUND(SUM(Revenue), 2)
     FROM sales) AS Total_Revenue
""", conn)

print("\nDATABASE VALIDATION:")
print(validation.to_string(index=False))

# ---------------------------- EXPORT VALIDATION ------------------------------

validation.to_csv(
    RESULTS_DIR / "database_validation.csv",
    index=False
)

tables.to_csv(
    RESULTS_DIR / "database_tables.csv",
    index=False
)

views.to_csv(
    RESULTS_DIR / "database_views.csv",
    index=False
)

conn.close()

print("\n" + "=" * 85)
print("DATABASE CREATED SUCCESSFULLY")
print("=" * 85)

print(f"Database path: {DATABASE_PATH}")
print("Tables: sales, customer_sales, cancellations")
print("Views: order_summary, customer_summary")
print("Indexes created for common analytical fields.")
print("\nNext: Run the SQL business analytics queries.")