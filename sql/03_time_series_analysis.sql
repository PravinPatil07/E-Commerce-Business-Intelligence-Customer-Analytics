-- =============================================================================
-- FILE: 03_time_series_analysis.sql
-- TIME SERIES & SALES TREND ANALYSIS
-- =============================================================================

-- QUERY 13: Monthly revenue, orders and customers
SELECT
    strftime('%Y-%m', InvoiceDate) AS year_month,
    ROUND(SUM(Revenue), 2) AS monthly_revenue,
    COUNT(DISTINCT InvoiceNo) AS monthly_orders,
    COUNT(DISTINCT CustomerID) AS monthly_customers,
    SUM(Quantity) AS units_sold,

    ROUND(
        SUM(Revenue) / NULLIF(COUNT(DISTINCT InvoiceNo), 0), 2
    ) AS monthly_average_order_value

FROM sales
GROUP BY year_month
ORDER BY year_month;


-- QUERY 14: Month-over-month revenue growth
WITH monthly_sales AS (
    SELECT
        strftime('%Y-%m', InvoiceDate) AS year_month,
        SUM(Revenue) AS revenue
    FROM sales
    GROUP BY year_month
),
growth AS (
    SELECT
        year_month,
        revenue,
        LAG(revenue) OVER (ORDER BY year_month) AS previous_revenue
    FROM monthly_sales
)
SELECT
    year_month,
    ROUND(revenue, 2) AS current_revenue,
    ROUND(previous_revenue, 2) AS previous_month_revenue,
    ROUND(revenue - previous_revenue, 2) AS revenue_change,
    ROUND(
        100.0 * (revenue - previous_revenue)
        / NULLIF(previous_revenue, 0),
        2
    ) AS mom_growth_percentage
FROM growth
ORDER BY year_month;


-- QUERY 15: Month-over-month order growth
WITH monthly_orders AS (
    SELECT
        strftime('%Y-%m', InvoiceDate) AS year_month,
        COUNT(DISTINCT InvoiceNo) AS orders
    FROM sales
    GROUP BY year_month
),
order_growth AS (
    SELECT
        year_month,
        orders,
        LAG(orders) OVER (ORDER BY year_month) AS previous_orders
    FROM monthly_orders
)
SELECT
    year_month,
    orders AS current_orders,
    previous_orders,
    orders - previous_orders AS order_change,
    ROUND(
        100.0 * (orders - previous_orders)
        / NULLIF(previous_orders, 0),
        2
    ) AS order_growth_percentage
FROM order_growth
ORDER BY year_month;


-- QUERY 16: Revenue and order performance by weekday
SELECT
    CASE CAST(strftime('%w', InvoiceDate) AS INTEGER)
        WHEN 0 THEN 'Sunday'
        WHEN 1 THEN 'Monday'
        WHEN 2 THEN 'Tuesday'
        WHEN 3 THEN 'Wednesday'
        WHEN 4 THEN 'Thursday'
        WHEN 5 THEN 'Friday'
        WHEN 6 THEN 'Saturday'
    END AS weekday,

    COUNT(DISTINCT InvoiceNo) AS orders,
    ROUND(SUM(Revenue), 2) AS revenue,
    SUM(Quantity) AS units_sold

FROM sales
GROUP BY strftime('%w', InvoiceDate)
ORDER BY CAST(strftime('%w', InvoiceDate) AS INTEGER);


-- QUERY 17: Hourly sales analysis
SELECT
    CAST(strftime('%H', InvoiceDate) AS INTEGER) AS sales_hour,
    COUNT(DISTINCT InvoiceNo) AS orders,
    ROUND(SUM(Revenue), 2) AS revenue,
    SUM(Quantity) AS units_sold
FROM sales
GROUP BY sales_hour
ORDER BY sales_hour;


-- QUERY 18: Monthly revenue ranking
WITH monthly_sales AS (
    SELECT
        strftime('%Y-%m', InvoiceDate) AS year_month,
        SUM(Revenue) AS revenue
    FROM sales
    GROUP BY year_month
)
SELECT
    year_month,
    ROUND(revenue, 2) AS revenue,
    RANK() OVER (ORDER BY revenue DESC) AS revenue_rank
FROM monthly_sales
ORDER BY revenue_rank;