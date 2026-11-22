-- =============================================================================
-- FILE: 05_customer_analysis.sql
-- CUSTOMER ANALYTICS
-- =============================================================================

-- QUERY 26: Top 20 customers by revenue
SELECT
    CustomerID,
    ROUND(SUM(Revenue), 2) AS total_revenue,
    COUNT(DISTINCT InvoiceNo) AS total_orders,
    SUM(Quantity) AS units_purchased,
    ROUND(
        SUM(Revenue) / NULLIF(COUNT(DISTINCT InvoiceNo), 0),
        2
    ) AS average_order_value
FROM customer_sales
GROUP BY CustomerID
ORDER BY total_revenue DESC
LIMIT 20;


-- QUERY 27: Repeat vs one-time customer comparison
WITH customer_summary AS (
    SELECT
        CustomerID,
        COUNT(DISTINCT InvoiceNo) AS order_count,
        SUM(Revenue) AS revenue
    FROM customer_sales
    GROUP BY CustomerID
)
SELECT
    CASE
        WHEN order_count = 1 THEN 'One-Time Customer'
        ELSE 'Repeat Customer'
    END AS customer_segment,
    COUNT(*) AS customers,
    ROUND(SUM(revenue), 2) AS segment_revenue,
    ROUND(
        100.0 * COUNT(*) / (SELECT COUNT(*) FROM customer_summary),
        2
    ) AS customer_percentage,
    ROUND(
        100.0 * SUM(revenue) / (SELECT SUM(revenue) FROM customer_summary),
        2
    ) AS revenue_percentage
FROM customer_summary
GROUP BY customer_segment
ORDER BY customers DESC;


-- QUERY 28: Customer purchase frequency
SELECT
    order_count AS number_of_orders,
    COUNT(*) AS number_of_customers,
    ROUND(SUM(customer_revenue), 2) AS total_customer_revenue
FROM (
    SELECT
        CustomerID,
        COUNT(DISTINCT InvoiceNo) AS order_count,
        SUM(Revenue) AS customer_revenue
    FROM customer_sales
    GROUP BY CustomerID
)
GROUP BY order_count
ORDER BY order_count;


-- QUERY 29: Customer lifetime summary
SELECT
    CustomerID,
    TotalOrders,
    ROUND(TotalRevenue, 2) AS total_revenue,
    TotalUnits,
    FirstPurchase,
    LastPurchase,
    ROUND(
        TotalRevenue / NULLIF(TotalOrders, 0),
        2
    ) AS average_order_value
FROM customer_summary
ORDER BY TotalRevenue DESC
LIMIT 30;


-- QUERY 30: Customer last purchase and inactivity days
WITH customer_activity AS (
    SELECT
        CustomerID,
        MAX(date(InvoiceDate)) AS last_purchase_date,
        COUNT(DISTINCT InvoiceNo) AS total_orders,
        SUM(Revenue) AS total_revenue
    FROM customer_sales
    GROUP BY CustomerID
),
dataset_snapshot AS (
    SELECT MAX(date(InvoiceDate)) AS snapshot_date
    FROM sales
)
SELECT
    c.CustomerID,
    c.last_purchase_date,
    c.total_orders,
    ROUND(c.total_revenue, 2) AS total_revenue,
    CAST(
        julianday(d.snapshot_date) - julianday(c.last_purchase_date)
        AS INTEGER
    ) AS days_since_last_purchase,
    CASE
        WHEN julianday(d.snapshot_date) - julianday(c.last_purchase_date) >= 90
            THEN 'Inactive 90+ Days'
        ELSE 'Active Within 90 Days'
    END AS activity_status
FROM customer_activity c
CROSS JOIN dataset_snapshot d
ORDER BY days_since_last_purchase DESC;


-- QUERY 31: Revenue concentration among customers
WITH customer_revenue AS (
    SELECT
        CustomerID,
        SUM(Revenue) AS revenue
    FROM customer_sales
    GROUP BY CustomerID
),
ranked_customers AS (
    SELECT
        CustomerID,
        revenue,
        RANK() OVER (ORDER BY revenue DESC) AS customer_rank,
        SUM(revenue) OVER (
            ORDER BY revenue DESC, CustomerID
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) AS cumulative_revenue
    FROM customer_revenue
)
SELECT
    CustomerID,
    ROUND(revenue, 2) AS customer_revenue,
    customer_rank,
    ROUND(cumulative_revenue, 2) AS cumulative_revenue,
    ROUND(
        100.0 * cumulative_revenue
        / (SELECT SUM(Revenue) FROM sales),
        2
    ) AS cumulative_revenue_percentage
FROM ranked_customers
ORDER BY customer_rank;


-- QUERY 32: Average customer revenue and order frequency
SELECT
    ROUND(AVG(TotalRevenue), 2) AS average_customer_revenue,
    ROUND(AVG(TotalOrders), 2) AS average_customer_orders,
    ROUND(AVG(TotalUnits), 2) AS average_customer_units,
    COUNT(*) AS total_identifiable_customers
FROM customer_summary;