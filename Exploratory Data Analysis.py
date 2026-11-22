# =============================================================================
# PHASE 3: EXPLORATORY DATA ANALYSIS (EDA)
# PROJECT: E-Commerce Business Intelligence & Customer Analytics
# =============================================================================
# This script:
# 1. Loads Phase 2 cleaned datasets
# 2. Calculates business KPIs
# 3. Performs sales, product, customer, country and time analysis
# 4. Generates visualizations
# 5. Exports analysis tables
# 6. Generates automated business insight summaries
#
# Outputs:
#   reports/phase3_eda_summary.json
#   reports/phase3_business_insights.txt
#   reports/eda_tables/*.csv
#   visualizations/phase3/*.png
# =============================================================================

from pathlib import Path
import json
import warnings

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

warnings.filterwarnings("ignore")

# Display tables properly when running Python scripts from the terminal
def display(obj):
    if isinstance(obj, pd.DataFrame):
        print(obj.to_string(index=False))
    elif isinstance(obj, pd.Series):
        print(obj.to_string())
    else:
        print(obj)

# =============================================================================
# 1. PROJECT CONFIGURATION
# =============================================================================

PROJECT_ROOT = Path.cwd()

DATA_DIR = PROJECT_ROOT / "data" / "processed"
REPORT_DIR = PROJECT_ROOT / "reports"
TABLE_DIR = REPORT_DIR / "eda_tables"
CHART_DIR = PROJECT_ROOT / "visualizations" / "phase3"

for directory in [REPORT_DIR, TABLE_DIR, CHART_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

sns.set_theme(style="whitegrid", context="notebook")

plt.rcParams["figure.figsize"] = (12, 6)
plt.rcParams["figure.dpi"] = 120
plt.rcParams["savefig.dpi"] = 160
plt.rcParams["axes.titleweight"] = "bold"

print("=" * 90)
print("PHASE 3: EXPLORATORY DATA ANALYSIS")
print("=" * 90)

print(f"Project root: {PROJECT_ROOT}")

# =============================================================================
# 2. LOAD CLEANED DATA
# =============================================================================

sales_file = DATA_DIR / "cleaned_sales.csv"
customer_file = DATA_DIR / "customer_eligible_sales.csv"
cancellation_file = DATA_DIR / "cancelled_transactions.csv"

if not sales_file.exists():
    raise FileNotFoundError(
        f"Cleaned sales dataset not found:\n{sales_file}\n"
        "Please complete Phase 2 first."
    )

sales = pd.read_csv(sales_file)

sales["InvoiceDate"] = pd.to_datetime(
    sales["InvoiceDate"], errors="coerce"
)

if "Revenue" not in sales.columns:
    sales["Revenue"] = sales["Quantity"] * sales["UnitPrice"]

# Use customer-eligible data if available, otherwise derive it
if customer_file.exists():
    customer_sales = pd.read_csv(customer_file)
    customer_sales["InvoiceDate"] = pd.to_datetime(
        customer_sales["InvoiceDate"], errors="coerce"
    )
else:
    customer_sales = sales[
        sales["CustomerID"].notna()
    ].copy()

if cancellation_file.exists():
    cancellations = pd.read_csv(cancellation_file)

    if "InvoiceDate" in cancellations.columns:
        cancellations["InvoiceDate"] = pd.to_datetime(
            cancellations["InvoiceDate"], errors="coerce"
        )
else:
    cancellations = pd.DataFrame()

# Ensure proper types
sales["Quantity"] = pd.to_numeric(
    sales["Quantity"], errors="coerce"
)

sales["UnitPrice"] = pd.to_numeric(
    sales["UnitPrice"], errors="coerce"
)

sales["Revenue"] = pd.to_numeric(
    sales["Revenue"], errors="coerce"
)

sales["InvoiceNo"] = sales["InvoiceNo"].astype(str)

customer_sales["CustomerID"] = pd.to_numeric(
    customer_sales["CustomerID"], errors="coerce"
)

sales = sales.dropna(
    subset=["InvoiceDate", "Revenue", "InvoiceNo"]
).copy()

customer_sales = customer_sales.dropna(
    subset=["CustomerID", "InvoiceDate"]
).copy()

customer_sales["CustomerID"] = (
    customer_sales["CustomerID"].astype("Int64")
)

print("\nDATA LOADED")
print("-" * 90)
print(f"Sales rows: {len(sales):,}")
print(f"Customer eligible rows: {len(customer_sales):,}")
print(f"Cancellation rows: {len(cancellations):,}")

# =============================================================================
# 3. HELPER FUNCTIONS
# =============================================================================

def save_table(df, filename):
    """Save an analysis table to the EDA tables folder."""
    path = TABLE_DIR / filename
    df.to_csv(path, index=False)
    print(f"Saved table: {path.name}")


def save_chart(filename):
    """Save the current matplotlib chart."""
    path = CHART_DIR / filename
    plt.tight_layout()
    plt.savefig(path, bbox_inches="tight")
    plt.close()
    print(f"Saved chart: {path.name}")


def money(value):
    return f"{value:,.2f}"


def percentage(value):
    return f"{value:.2f}%"


def safe_divide(a, b):
    return a / b if b else 0


# =============================================================================
# 4. KPI ANALYSIS
# =============================================================================

total_revenue = float(sales["Revenue"].sum())

total_orders = int(
    sales["InvoiceNo"].nunique()
)

total_customers = int(
    customer_sales["CustomerID"].nunique()
)

total_products = int(
    sales["StockCode"].nunique()
)

total_units_sold = int(
    sales["Quantity"].sum()
)

average_order_value = safe_divide(
    total_revenue,
    total_orders
)

average_revenue_per_customer = safe_divide(
    total_revenue,
    total_customers
)

customer_order_counts = (
    customer_sales.groupby("CustomerID")["InvoiceNo"]
    .nunique()
)

repeat_customers = int(
    (customer_order_counts > 1).sum()
)

one_time_customers = int(
    (customer_order_counts == 1).sum()
)

repeat_customer_percentage = safe_divide(
    repeat_customers,
    total_customers
) * 100

repeat_order_customers = customer_sales[
    customer_sales["CustomerID"].isin(
        customer_order_counts[customer_order_counts > 1].index
    )
]

repeat_customer_revenue = float(
    repeat_order_customers["Revenue"].sum()
)

repeat_customer_revenue_percentage = safe_divide(
    repeat_customer_revenue,
    total_revenue
) * 100

first_date = sales["InvoiceDate"].min()
last_date = sales["InvoiceDate"].max()

kpi_summary = pd.DataFrame({
    "KPI": [
        "Total Revenue",
        "Total Orders",
        "Unique Customers",
        "Unique Products",
        "Total Units Sold",
        "Average Order Value",
        "Average Revenue per Customer",
        "Repeat Customers",
        "One-Time Customers",
        "Repeat Customer Percentage",
        "Revenue from Repeat Customers",
        "Repeat Customer Revenue Percentage"
    ],
    "Value": [
        total_revenue,
        total_orders,
        total_customers,
        total_products,
        total_units_sold,
        average_order_value,
        average_revenue_per_customer,
        repeat_customers,
        one_time_customers,
        repeat_customer_percentage,
        repeat_customer_revenue,
        repeat_customer_revenue_percentage
    ]
})

print("\n" + "=" * 90)
print("BUSINESS KPI SUMMARY")
print("=" * 90)

display(kpi_summary)

save_table(kpi_summary, "kpi_summary.csv")

# =============================================================================
# 5. MONTHLY REVENUE ANALYSIS
# =============================================================================

sales["YearMonth"] = (
    sales["InvoiceDate"].dt.to_period("M")
)

monthly_revenue = (
    sales.groupby("YearMonth")
    .agg(
        Revenue=("Revenue", "sum"),
        Orders=("InvoiceNo", "nunique"),
        Units_Sold=("Quantity", "sum")
    )
    .reset_index()
)

monthly_revenue["YearMonth"] = (
    monthly_revenue["YearMonth"].astype(str)
)

monthly_revenue["Revenue_Growth_Percentage"] = (
    monthly_revenue["Revenue"].pct_change() * 100
)

monthly_revenue["Order_Growth_Percentage"] = (
    monthly_revenue["Orders"].pct_change() * 100
)

monthly_revenue["Average_Order_Value"] = (
    monthly_revenue["Revenue"]
    / monthly_revenue["Orders"].replace(0, np.nan)
)

print("\nMONTHLY BUSINESS PERFORMANCE")
display(monthly_revenue)

save_table(monthly_revenue, "monthly_revenue_analysis.csv")

# Revenue trend
plt.figure(figsize=(14, 6))

sns.lineplot(
    data=monthly_revenue,
    x="YearMonth",
    y="Revenue",
    marker="o"
)

plt.title("Monthly Revenue Trend")
plt.xlabel("Month")
plt.ylabel("Revenue")
plt.xticks(rotation=45)

save_chart("monthly_revenue.png")

# =============================================================================
# 6. MONTHLY ORDER ANALYSIS
# =============================================================================

plt.figure(figsize=(14, 6))

sns.lineplot(
    data=monthly_revenue,
    x="YearMonth",
    y="Orders",
    marker="o"
)

plt.title("Monthly Number of Orders")
plt.xlabel("Month")
plt.ylabel("Number of Orders")
plt.xticks(rotation=45)

save_chart("monthly_orders.png")

# =============================================================================
# 7. MONTHLY CUSTOMER ACTIVITY
# =============================================================================

monthly_customers = (
    customer_sales.assign(
        YearMonth=customer_sales["InvoiceDate"].dt.to_period("M")
    )
    .groupby("YearMonth")
    .agg(
        Active_Customers=("CustomerID", "nunique"),
        Orders=("InvoiceNo", "nunique"),
        Revenue=("Revenue", "sum")
    )
    .reset_index()
)

monthly_customers["YearMonth"] = (
    monthly_customers["YearMonth"].astype(str)
)

print("\nMONTHLY CUSTOMER ACTIVITY")
display(monthly_customers)

save_table(monthly_customers, "monthly_customer_activity.csv")

plt.figure(figsize=(14, 6))

sns.lineplot(
    data=monthly_customers,
    x="YearMonth",
    y="Active_Customers",
    marker="o"
)

plt.title("Monthly Active Customers")
plt.xlabel("Month")
plt.ylabel("Active Customers")
plt.xticks(rotation=45)

save_chart("monthly_customers.png")

# =============================================================================
# 8. DAY-OF-WEEK ANALYSIS
# =============================================================================

sales["DayOfWeek"] = sales["InvoiceDate"].dt.day_name()

weekday_order = [
    "Monday", "Tuesday", "Wednesday",
    "Thursday", "Friday", "Saturday", "Sunday"
]

weekday_analysis = (
    sales.groupby("DayOfWeek")
    .agg(
        Revenue=("Revenue", "sum"),
        Orders=("InvoiceNo", "nunique"),
        Units_Sold=("Quantity", "sum")
    )
    .reindex(weekday_order)
    .reset_index()
)

print("\nDAY-OF-WEEK ANALYSIS")
display(weekday_analysis)

save_table(weekday_analysis, "weekday_analysis.csv")

plt.figure(figsize=(12, 6))

sns.barplot(
    data=weekday_analysis,
    x="DayOfWeek",
    y="Revenue"
)

plt.title("Revenue by Day of Week")
plt.xlabel("Day of Week")
plt.ylabel("Revenue")
plt.xticks(rotation=30)

save_chart("sales_by_weekday.png")

# =============================================================================
# 9. HOURLY SALES ANALYSIS
# =============================================================================

sales["Hour"] = sales["InvoiceDate"].dt.hour

hourly_analysis = (
    sales.groupby("Hour")
    .agg(
        Revenue=("Revenue", "sum"),
        Orders=("InvoiceNo", "nunique"),
        Units_Sold=("Quantity", "sum")
    )
    .reset_index()
)

print("\nHOURLY SALES ANALYSIS")
display(hourly_analysis)

save_table(hourly_analysis, "hourly_sales_analysis.csv")

plt.figure(figsize=(12, 6))

sns.barplot(
    data=hourly_analysis,
    x="Hour",
    y="Orders"
)

plt.title("Orders by Hour of Day")
plt.xlabel("Hour")
plt.ylabel("Orders")
plt.xticks(range(0, 24))

save_chart("sales_by_hour.png")

# =============================================================================
# 10. PRODUCT PERFORMANCE ANALYSIS
# =============================================================================

product_analysis = (
    sales.groupby("StockCode")
    .agg(
        Product_Description=("Description", "first"),
        Revenue=("Revenue", "sum"),
        Units_Sold=("Quantity", "sum"),
        Orders=("InvoiceNo", "nunique"),
        Average_Unit_Price=("UnitPrice", "mean")
    )
    .reset_index()
)

product_analysis = product_analysis.sort_values(
    "Revenue", ascending=False
)

product_analysis["Revenue_Contribution_Percentage"] = (
    product_analysis["Revenue"] / total_revenue * 100
)

product_analysis["Cumulative_Revenue_Percentage"] = (
    product_analysis["Revenue_Contribution_Percentage"].cumsum()
)

print("\nTOP 20 PRODUCTS BY REVENUE")
display(product_analysis.head(20))

save_table(product_analysis, "product_performance.csv")

# Top products chart
top_products = product_analysis.head(15).copy()

top_products["Product_Label"] = (
    top_products["StockCode"].astype(str)
    + " - "
    + top_products["Product_Description"].astype(str).str.slice(0, 35)
)

plt.figure(figsize=(14, 8))

sns.barplot(
    data=top_products,
    x="Revenue",
    y="Product_Label"
)

plt.title("Top 15 Products by Revenue")
plt.xlabel("Revenue")
plt.ylabel("Product")

save_chart("top_products.png")

# =============================================================================
# 11. PRODUCT QUANTITY VS REVENUE
# =============================================================================

product_scatter = product_analysis.copy()

# Remove extremely large values from the visualization only,
# using percentile limits to keep the scatter readable.
quantity_limit = product_scatter["Units_Sold"].quantile(0.99)
revenue_limit = product_scatter["Revenue"].quantile(0.99)

scatter_data = product_scatter[
    (product_scatter["Units_Sold"] <= quantity_limit)
    & (product_scatter["Revenue"] <= revenue_limit)
]

plt.figure(figsize=(12, 7))

sns.scatterplot(
    data=scatter_data,
    x="Units_Sold",
    y="Revenue",
    alpha=0.65
)

plt.title("Product Sales Volume vs Revenue")
plt.xlabel("Units Sold")
plt.ylabel("Revenue")

save_chart("product_quantity_vs_revenue.png")

# =============================================================================
# 12. COUNTRY ANALYSIS
# =============================================================================

country_analysis = (
    sales.groupby("Country")
    .agg(
        Revenue=("Revenue", "sum"),
        Orders=("InvoiceNo", "nunique"),
        Units_Sold=("Quantity", "sum"),
        Customers=("CustomerID", "nunique")
    )
    .reset_index()
)

country_analysis["Revenue_Contribution_Percentage"] = (
    country_analysis["Revenue"] / total_revenue * 100
)

country_analysis["Average_Order_Value"] = (
    country_analysis["Revenue"]
    / country_analysis["Orders"].replace(0, np.nan)
)

country_analysis = country_analysis.sort_values(
    "Revenue", ascending=False
)

print("\nTOP 20 COUNTRIES BY REVENUE")
display(country_analysis.head(20))

save_table(country_analysis, "country_analysis.csv")

top_countries = country_analysis.head(15)

plt.figure(figsize=(14, 8))

sns.barplot(
    data=top_countries,
    x="Revenue",
    y="Country"
)

plt.title("Top 15 Countries by Revenue")
plt.xlabel("Revenue")
plt.ylabel("Country")

save_chart("country_revenue.png")

# =============================================================================
# 13. CUSTOMER SPENDING ANALYSIS
# =============================================================================

customer_analysis = (
    customer_sales.groupby("CustomerID")
    .agg(
        Revenue=("Revenue", "sum"),
        Orders=("InvoiceNo", "nunique"),
        Units_Sold=("Quantity", "sum"),
        First_Purchase=("InvoiceDate", "min"),
        Last_Purchase=("InvoiceDate", "max")
    )
    .reset_index()
)

customer_analysis["Average_Order_Value"] = (
    customer_analysis["Revenue"]
    / customer_analysis["Orders"].replace(0, np.nan)
)

customer_analysis["Days_Between_First_And_Last_Purchase"] = (
    customer_analysis["Last_Purchase"]
    - customer_analysis["First_Purchase"]
).dt.days

customer_analysis["Revenue_Contribution_Percentage"] = (
    customer_analysis["Revenue"] / total_revenue * 100
)

customer_analysis = customer_analysis.sort_values(
    "Revenue", ascending=False
)

print("\nTOP 20 CUSTOMERS BY REVENUE")
display(customer_analysis.head(20))

save_table(customer_analysis, "customer_analysis.csv")

# Customer revenue histogram
plt.figure(figsize=(12, 6))

sns.histplot(
    customer_analysis["Revenue"],
    bins=50,
    kde=True
)

plt.title("Distribution of Customer Revenue")
plt.xlabel("Customer Revenue")
plt.ylabel("Number of Customers")

save_chart("customer_spending.png")

# =============================================================================
# 14. CUSTOMER ORDER FREQUENCY
# =============================================================================

frequency_distribution = (
    customer_analysis.groupby("Orders")
    .agg(
        Customers=("CustomerID", "count"),
        Total_Revenue=("Revenue", "sum")
    )
    .reset_index()
)

frequency_distribution = frequency_distribution.sort_values(
    "Orders"
)

print("\nCUSTOMER PURCHASE FREQUENCY")
display(frequency_distribution.head(30))

save_table(
    frequency_distribution,
    "customer_order_frequency.csv"
)

# =============================================================================
# 15. REPEAT VS ONE-TIME CUSTOMER ANALYSIS
# =============================================================================

customer_analysis["Customer_Type"] = np.where(
    customer_analysis["Orders"] > 1,
    "Repeat Customer",
    "One-Time Customer"
)

customer_type_analysis = (
    customer_analysis.groupby("Customer_Type")
    .agg(
        Customers=("CustomerID", "count"),
        Revenue=("Revenue", "sum"),
        Orders=("Orders", "sum")
    )
    .reset_index()
)

customer_type_analysis["Customer_Percentage"] = (
    customer_type_analysis["Customers"]
    / customer_type_analysis["Customers"].sum()
    * 100
)

customer_type_analysis["Revenue_Percentage"] = (
    customer_type_analysis["Revenue"]
    / customer_type_analysis["Revenue"].sum()
    * 100
)

print("\nREPEAT VS ONE-TIME CUSTOMER ANALYSIS")
display(customer_type_analysis)

save_table(
    customer_type_analysis,
    "repeat_customer_analysis.csv"
)

# =============================================================================
# 16. CUSTOMER REVENUE CONCENTRATION (PARETO)
# =============================================================================

customer_revenue_rank = (
    customer_analysis.sort_values(
        "Revenue", ascending=False
    ).copy()
)

customer_revenue_rank["Cumulative_Revenue"] = (
    customer_revenue_rank["Revenue"].cumsum()
)

customer_revenue_rank["Cumulative_Revenue_Percentage"] = (
    customer_revenue_rank["Cumulative_Revenue"]
    / total_revenue * 100
)

customer_revenue_rank["Customer_Rank"] = (
    np.arange(1, len(customer_revenue_rank) + 1)
)

save_table(
    customer_revenue_rank,
    "customer_revenue_concentration.csv"
)

# Calculate revenue contributed by top customer groups
top_1_percent_count = max(
    1, int(np.ceil(len(customer_revenue_rank) * 0.01))
)

top_5_percent_count = max(
    1, int(np.ceil(len(customer_revenue_rank) * 0.05))
)

top_10_percent_count = max(
    1, int(np.ceil(len(customer_revenue_rank) * 0.10))
)

top_1_percent_revenue = (
    customer_revenue_rank.head(top_1_percent_count)["Revenue"].sum()
    / total_revenue * 100
)

top_5_percent_revenue = (
    customer_revenue_rank.head(top_5_percent_count)["Revenue"].sum()
    / total_revenue * 100
)

top_10_percent_revenue = (
    customer_revenue_rank.head(top_10_percent_count)["Revenue"].sum()
    / total_revenue * 100
)

concentration_summary = pd.DataFrame({
    "Customer_Group": [
        "Top 1% Customers",
        "Top 5% Customers",
        "Top 10% Customers"
    ],
    "Revenue_Contribution_Percentage": [
        top_1_percent_revenue,
        top_5_percent_revenue,
        top_10_percent_revenue
    ]
})

print("\nCUSTOMER REVENUE CONCENTRATION")
display(concentration_summary)

save_table(
    concentration_summary,
    "revenue_concentration_summary.csv"
)

# Pareto plot
plot_count = min(100, len(customer_revenue_rank))

pareto_data = customer_revenue_rank.head(plot_count)

fig, ax1 = plt.subplots(figsize=(14, 7))

ax1.bar(
    pareto_data["Customer_Rank"],
    pareto_data["Revenue"]
)

ax1.set_xlabel("Customer Rank")
ax1.set_ylabel("Customer Revenue")
ax1.set_title("Customer Revenue Concentration - Pareto Analysis")

ax2 = ax1.twinx()

ax2.plot(
    pareto_data["Customer_Rank"],
    pareto_data["Cumulative_Revenue_Percentage"],
    marker=".",
    linewidth=2
)

ax2.set_ylabel("Cumulative Revenue Percentage")
ax2.set_ylim(0, 100)

save_chart("revenue_concentration.png")

# =============================================================================
# 17. ORDER VALUE ANALYSIS
# =============================================================================

order_analysis = (
    sales.groupby("InvoiceNo")
    .agg(
        Order_Revenue=("Revenue", "sum"),
        Units=("Quantity", "sum"),
        CustomerID=("CustomerID", "first"),
        InvoiceDate=("InvoiceDate", "first"),
        Products=("StockCode", "nunique")
    )
    .reset_index()
)

order_analysis = order_analysis[
    order_analysis["Order_Revenue"] > 0
].copy()

print("\nORDER VALUE SUMMARY")
display(order_analysis["Order_Revenue"].describe())

save_table(
    order_analysis,
    "order_level_analysis.csv"
)

plt.figure(figsize=(12, 6))

sns.histplot(
    order_analysis["Order_Revenue"],
    bins=60,
    kde=True
)

plt.title("Distribution of Order Revenue")
plt.xlabel("Order Revenue")
plt.ylabel("Number of Orders")

save_chart("order_value_distribution.png")

# Boxplot
plt.figure(figsize=(12, 5))

sns.boxplot(
    x=order_analysis["Order_Revenue"]
)

plt.title("Order Revenue - Boxplot")
plt.xlabel("Order Revenue")

save_chart("order_value_boxplot.png")

# =============================================================================
# 18. CANCELLATION ANALYSIS
# =============================================================================

cancellation_summary = {}

if not cancellations.empty:

    cancellation_summary["Cancellation_Rows"] = int(
        len(cancellations)
    )

    if "InvoiceNo" in cancellations.columns:
        cancellation_summary["Cancelled_Invoices"] = int(
            cancellations["InvoiceNo"].nunique()
        )

    if "Quantity" in cancellations.columns:
        cancellation_summary["Cancellation_Quantity"] = int(
            pd.to_numeric(
                cancellations["Quantity"],
                errors="coerce"
            ).sum()
        )

    if "UnitPrice" in cancellations.columns:
        cancellations["UnitPrice"] = pd.to_numeric(
            cancellations["UnitPrice"],
            errors="coerce"
        )

    if {"Quantity", "UnitPrice"}.issubset(cancellations.columns):
        cancellation_summary["Cancellation_Value_Proxy"] = float(
            (
                cancellations["Quantity"]
                * cancellations["UnitPrice"]
            ).sum()
        )

    if "InvoiceDate" in cancellations.columns:
        cancellation_monthly = (
            cancellations.dropna(subset=["InvoiceDate"])
            .assign(
                YearMonth=lambda x:
                x["InvoiceDate"].dt.to_period("M")
            )
            .groupby("YearMonth")
            .agg(
                Cancellation_Rows=("InvoiceNo", "count")
            )
            .reset_index()
        )

        cancellation_monthly["YearMonth"] = (
            cancellation_monthly["YearMonth"].astype(str)
        )

        save_table(
            cancellation_monthly,
            "monthly_cancellation_analysis.csv"
        )

        plt.figure(figsize=(14, 6))

        sns.lineplot(
            data=cancellation_monthly,
            x="YearMonth",
            y="Cancellation_Rows",
            marker="o"
        )

        plt.title("Monthly Cancellation Records")
        plt.xlabel("Month")
        plt.ylabel("Cancellation Records")
        plt.xticks(rotation=45)

        save_chart("monthly_cancellations.png")

    print("\nCANCELLATION SUMMARY")
    display(pd.DataFrame(
        list(cancellation_summary.items()),
        columns=["Metric", "Value"]
    ))

else:
    print("\nNo cancellation file found or cancellation dataset is empty.")

# =============================================================================
# 19. PRODUCT REVENUE PARETO ANALYSIS
# =============================================================================

product_pareto = product_analysis.sort_values(
    "Revenue", ascending=False
).copy()

product_pareto["Cumulative_Revenue"] = (
    product_pareto["Revenue"].cumsum()
)

product_pareto["Cumulative_Revenue_Percentage"] = (
    product_pareto["Cumulative_Revenue"]
    / total_revenue * 100
)

save_table(
    product_pareto,
    "product_revenue_concentration.csv"
)

products_for_80_percent = int(
    (
        product_pareto["Cumulative_Revenue_Percentage"] <= 80
    ).sum() + 1
)

product_80_percent_share = safe_divide(
    products_for_80_percent,
    len(product_pareto)
) * 100

# =============================================================================
# 20. BUSINESS INSIGHT GENERATION
# =============================================================================

best_month = (
    monthly_revenue.sort_values(
        "Revenue", ascending=False
    ).head(1)
)

worst_month = (
    monthly_revenue.sort_values(
        "Revenue", ascending=True
    ).head(1)
)

best_weekday = (
    weekday_analysis.sort_values(
        "Revenue", ascending=False
    ).head(1)
)

best_hour = (
    hourly_analysis.sort_values(
        "Orders", ascending=False
    ).head(1)
)

best_product = (
    product_analysis.sort_values(
        "Revenue", ascending=False
    ).head(1)
)

best_country = (
    country_analysis.sort_values(
        "Revenue", ascending=False
    ).head(1)
)

top_customer = (
    customer_analysis.sort_values(
        "Revenue", ascending=False
    ).head(1)
)

insights = []

insights.append("=" * 90)
insights.append("PHASE 3: BUSINESS INSIGHTS")
insights.append("E-COMMERCE BUSINESS INTELLIGENCE & CUSTOMER ANALYTICS")
insights.append("=" * 90)

insights.append("\n1. OVERALL BUSINESS PERFORMANCE")
insights.append(f"Total revenue: {money(total_revenue)}")
insights.append(f"Total orders: {total_orders:,}")
insights.append(f"Unique customers with IDs: {total_customers:,}")
insights.append(f"Unique products: {total_products:,}")
insights.append(f"Units sold: {total_units_sold:,}")
insights.append(f"Average order value: {money(average_order_value)}")
insights.append(f"Revenue/customer: {money(average_revenue_per_customer)}")
insights.append(f"Analysis period: {first_date} to {last_date}")

insights.append("\n2. MONTHLY REVENUE PERFORMANCE")

if not best_month.empty:
    insights.append(
        f"Highest-revenue month: {best_month.iloc[0]['YearMonth']} "
        f"with revenue {money(best_month.iloc[0]['Revenue'])}"
    )

if not worst_month.empty:
    insights.append(
        f"Lowest-revenue month: {worst_month.iloc[0]['YearMonth']} "
        f"with revenue {money(worst_month.iloc[0]['Revenue'])}"
    )

insights.append("\n3. CUSTOMER BEHAVIOR")
insights.append(f"Repeat customers: {repeat_customers:,}")
insights.append(f"One-time customers: {one_time_customers:,}")
insights.append(
    f"Repeat customer percentage: {percentage(repeat_customer_percentage)}"
)
insights.append(
    f"Repeat-customer revenue contribution: "
    f"{percentage(repeat_customer_revenue_percentage)}"
)

insights.append("\n4. PRODUCT PERFORMANCE")

if not best_product.empty:
    insights.append(
        f"Highest-revenue product: "
        f"{best_product.iloc[0]['StockCode']} - "
        f"{best_product.iloc[0]['Product_Description']}"
    )

    insights.append(
        f"Product revenue: {money(best_product.iloc[0]['Revenue'])}"
    )

insights.append(
    f"Products required to reach approximately 80% revenue: "
    f"{products_for_80_percent:,}"
)

insights.append(
    f"These products represent approximately "
    f"{product_80_percent_share:.2f}% of the total product catalog."
)

insights.append("\n5. GEOGRAPHIC PERFORMANCE")

if not best_country.empty:
    insights.append(
        f"Highest-revenue country: {best_country.iloc[0]['Country']}"
    )

    insights.append(
        f"Country revenue: {money(best_country.iloc[0]['Revenue'])}"
    )

    insights.append(
        f"Country revenue contribution: "
        f"{percentage(best_country.iloc[0]['Revenue_Contribution_Percentage'])}"
    )

insights.append("\n6. CUSTOMER REVENUE CONCENTRATION")
insights.append(
    f"Top 1% of customers account for approximately "
    f"{percentage(top_1_percent_revenue)} of revenue."
)
insights.append(
    f"Top 5% of customers account for approximately "
    f"{percentage(top_5_percent_revenue)} of revenue."
)
insights.append(
    f"Top 10% of customers account for approximately "
    f"{percentage(top_10_percent_revenue)} of revenue."
)

if not top_customer.empty:
    insights.append(
        f"Highest-spending customer ID: "
        f"{top_customer.iloc[0]['CustomerID']}"
    )
    insights.append(
        f"Customer revenue: {money(top_customer.iloc[0]['Revenue'])}"
    )

insights.append("\n7. SALES TIMING")

if not best_weekday.empty:
    insights.append(
        f"Highest-revenue weekday: "
        f"{best_weekday.iloc[0]['DayOfWeek']}"
    )

if not best_hour.empty:
    insights.append(
        f"Hour with most orders: {int(best_hour.iloc[0]['Hour'])}:00"
    )

insights.append("\n8. BUSINESS RECOMMENDATIONS")

insights.append(
    "- Investigate the strongest and weakest revenue months "
    "to understand seasonality and demand changes."
)

insights.append(
    "- Develop retention strategies for repeat customers "
    "while improving the conversion of one-time customers."
)

insights.append(
    "- Investigate top-performing products for stock planning "
    "and merchandising opportunities."
)

insights.append(
    "- Evaluate geographic markets based on revenue, orders "
    "and customer activity."
)

insights.append(
    "- Use customer revenue concentration to evaluate business "
    "dependency on high-value customers."
)

insights.append(
    "- Investigate cancellation patterns before interpreting "
    "cancellation values as lost revenue."
)

insights.append(
    "- These are descriptive findings, not causal conclusions. "
    "Further analysis is required before attributing changes "
    "to specific business actions."
)

insights_text = "\n".join(insights)

insights_file = REPORT_DIR / "phase3_business_insights.txt"

with open(
    insights_file,
    "w",
    encoding="utf-8"
) as file:
    file.write(insights_text)

print("\n" + insights_text)

# =============================================================================
# 21. EXPORT PHASE 3 SUMMARY
# =============================================================================

phase3_summary = {
    "project": "E-Commerce Business Intelligence & Customer Analytics",
    "phase": "Phase 3 - Exploratory Data Analysis",
    "analysis_start_date": str(first_date),
    "analysis_end_date": str(last_date),
    "kpis": {
        "total_revenue": round(total_revenue, 2),
        "total_orders": total_orders,
        "unique_customers": total_customers,
        "unique_products": total_products,
        "units_sold": total_units_sold,
        "average_order_value": round(average_order_value, 2),
        "average_revenue_per_customer": round(
            average_revenue_per_customer, 2
        ),
        "repeat_customers": repeat_customers,
        "one_time_customers": one_time_customers,
        "repeat_customer_percentage": round(
            repeat_customer_percentage, 2
        ),
        "repeat_customer_revenue_percentage": round(
            repeat_customer_revenue_percentage, 2
        )
    },
    "customer_revenue_concentration": {
        "top_1_percent_revenue_percentage": round(
            float(top_1_percent_revenue), 2
        ),
        "top_5_percent_revenue_percentage": round(
            float(top_5_percent_revenue), 2
        ),
        "top_10_percent_revenue_percentage": round(
            float(top_10_percent_revenue), 2
        )
    },
    "product_concentration": {
        "products_to_reach_80_percent_revenue": int(
            products_for_80_percent
        ),
        "product_catalog_percentage": round(
            float(product_80_percent_share), 2
        )
    },
    "cancellation_analysis": cancellation_summary
}

summary_file = REPORT_DIR / "phase3_eda_summary.json"

with open(
    summary_file,
    "w",
    encoding="utf-8"
) as file:
    json.dump(
        phase3_summary,
        file,
        indent=4,
        ensure_ascii=False
    )

# =============================================================================
# 22. FINAL REPORT
# =============================================================================

print("\n" + "=" * 90)
print("PHASE 3 COMPLETED SUCCESSFULLY")
print("=" * 90)

print("\nGenerated outputs:")

print("\nReports:")
for file in sorted(REPORT_DIR.glob("phase3*")):
    print(f"  {file.name}")

print("\nEDA tables:")
for file in sorted(TABLE_DIR.glob("*.csv")):
    print(f"  {file.name}")

print("\nVisualizations:")
for file in sorted(CHART_DIR.glob("*.png")):
    print(f"  {file.name}")

print("\n" + "=" * 90)
print("NEXT PHASE: PHASE 4 - SQL BUSINESS ANALYTICS")
print("=" * 90)