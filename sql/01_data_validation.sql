-- =============================================================================
-- FILE: 01_data_validation.sql
-- PHASE 4: DATA VALIDATION
-- =============================================================================

-- QUERY 1: Database table row counts
SELECT 'sales' AS table_name, COUNT(*) AS row_count FROM sales
UNION ALL
SELECT 'customer_sales', COUNT(*) FROM customer_sales
UNION ALL
SELECT 'cancellations', COUNT(*) FROM cancellations;


-- QUERY 2: Inspect sales table columns
PRAGMA table_info(sales);


-- QUERY 3: Missing values
SELECT
    SUM(CASE WHEN CustomerID IS NULL THEN 1 ELSE 0 END) AS missing_customer_ids,
    SUM(CASE WHEN Description IS NULL THEN 1 ELSE 0 END) AS missing_descriptions,
    SUM(CASE WHEN InvoiceDate IS NULL THEN 1 ELSE 0 END) AS missing_dates,
    SUM(CASE WHEN StockCode IS NULL THEN 1 ELSE 0 END) AS missing_stock_codes,
    SUM(CASE WHEN Country IS NULL THEN 1 ELSE 0 END) AS missing_countries
FROM sales;


-- QUERY 4: Invalid quantity, price and revenue
SELECT
    COUNT(*) AS total_records,
    SUM(CASE WHEN Quantity <= 0 THEN 1 ELSE 0 END) AS nonpositive_quantity,
    SUM(CASE WHEN UnitPrice <= 0 THEN 1 ELSE 0 END) AS nonpositive_price,
    SUM(CASE WHEN Revenue <= 0 THEN 1 ELSE 0 END) AS nonpositive_revenue
FROM sales;


-- QUERY 5: Check duplicate transaction lines
SELECT
    InvoiceNo,
    StockCode,
    CustomerID,
    InvoiceDate,
    Quantity,
    UnitPrice,
    COUNT(*) AS duplicate_count
FROM sales
GROUP BY
    InvoiceNo,
    StockCode,
    CustomerID,
    InvoiceDate,
    Quantity,
    UnitPrice
HAVING COUNT(*) > 1
ORDER BY duplicate_count DESC;


-- QUERY 6: Dataset date range
SELECT
    MIN(InvoiceDate) AS first_transaction,
    MAX(InvoiceDate) AS last_transaction,
    COUNT(DISTINCT date(InvoiceDate)) AS active_transaction_days
FROM sales;


-- QUERY 7: Validate customer eligibility table
SELECT
    COUNT(*) AS customer_sales_rows,
    COUNT(DISTINCT CustomerID) AS unique_customers,
    SUM(CASE WHEN CustomerID IS NULL THEN 1 ELSE 0 END) AS missing_customer_ids
FROM customer_sales;