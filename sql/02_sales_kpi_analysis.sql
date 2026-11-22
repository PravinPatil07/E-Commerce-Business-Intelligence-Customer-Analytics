-- =============================================================================
-- FILE: 02_sales_kpi_analysis.sql
-- EXECUTIVE KPI & SALES ANALYSIS
-- =============================================================================

-- QUERY 8: Executive KPI dashboard
SELECT
    ROUND(SUM(Revenue), 2) AS total_revenue,
    COUNT(DISTINCT InvoiceNo) AS total_orders,
    COUNT(DISTINCT CustomerID) AS identifiable_customers,
    COUNT(DISTINCT StockCode) AS unique_products,
    SUM(Quantity) AS units_sold,

    ROUND(
        SUM(Revenue) / NULLIF(COUNT(DISTINCT InvoiceNo), 0), 2
    ) AS average_order_value,

    ROUND(
        SUM(Revenue) / NULLIF(COUNT(DISTINCT CustomerID), 0), 2
    ) AS revenue_per_identifiable_customer

FROM sales;


-- QUERY 9: Yearly performance
SELECT
    strftime('%Y', InvoiceDate) AS sales_year,
    ROUND(SUM(Revenue), 2) AS yearly_revenue,
    COUNT(DISTINCT InvoiceNo) AS yearly_orders,
    COUNT(DISTINCT CustomerID) AS yearly_customers,
    SUM(Quantity) AS yearly_units_sold
FROM sales
GROUP BY sales_year
ORDER BY sales_year;


-- QUERY 10: Order-level summary
SELECT
    InvoiceNo,
    MIN(InvoiceDate) AS order_date,
    CustomerID,
    COUNT(DISTINCT StockCode) AS unique_products,
    SUM(Quantity) AS units_in_order,
    ROUND(SUM(Revenue), 2) AS order_revenue
FROM sales
GROUP BY InvoiceNo, CustomerID
ORDER BY order_revenue DESC;


-- QUERY 11: Order value distribution summary
WITH order_values AS (
    SELECT
        InvoiceNo,
        SUM(Revenue) AS order_revenue
    FROM sales
    GROUP BY InvoiceNo
)
SELECT
    COUNT(*) AS orders,
    ROUND(AVG(order_revenue), 2) AS average_order_value,
    ROUND(MIN(order_revenue), 2) AS minimum_order_value,
    ROUND(MAX(order_revenue), 2) AS maximum_order_value,
    ROUND(SUM(order_revenue), 2) AS total_revenue
FROM order_values
WHERE order_revenue > 0;


-- QUERY 12: Orders grouped into order-value ranges
WITH order_values AS (
    SELECT
        InvoiceNo,
        SUM(Revenue) AS order_revenue
    FROM sales
    GROUP BY InvoiceNo
)
SELECT
    CASE
        WHEN order_revenue < 25 THEN 'Under 25'
        WHEN order_revenue < 50 THEN '25 - 49.99'
        WHEN order_revenue < 100 THEN '50 - 99.99'
        WHEN order_revenue < 250 THEN '100 - 249.99'
        ELSE '250 and above'
    END AS order_value_segment,
    COUNT(*) AS order_count,
    ROUND(SUM(order_revenue), 2) AS segment_revenue
FROM order_values
WHERE order_revenue > 0
GROUP BY order_value_segment
ORDER BY MIN(order_revenue);