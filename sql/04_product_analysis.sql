-- =============================================================================
-- FILE: 04_product_analysis.sql
-- PRODUCT PERFORMANCE ANALYSIS
-- =============================================================================

-- QUERY 19: Top 20 products by revenue
SELECT
    StockCode,
    Description,
    ROUND(SUM(Revenue), 2) AS total_revenue,
    SUM(Quantity) AS units_sold,
    COUNT(DISTINCT InvoiceNo) AS orders,
    ROUND(AVG(UnitPrice), 2) AS average_unit_price
FROM sales
GROUP BY StockCode, Description
ORDER BY total_revenue DESC
LIMIT 20;


-- QUERY 20: Top 20 products by quantity sold
SELECT
    StockCode,
    Description,
    SUM(Quantity) AS units_sold,
    ROUND(SUM(Revenue), 2) AS revenue,
    COUNT(DISTINCT InvoiceNo) AS orders
FROM sales
GROUP BY StockCode, Description
ORDER BY units_sold DESC
LIMIT 20;


-- QUERY 21: Product revenue contribution percentage
WITH product_revenue AS (
    SELECT
        StockCode,
        Description,
        SUM(Revenue) AS revenue
    FROM sales
    GROUP BY StockCode, Description
)
SELECT
    StockCode,
    Description,
    ROUND(revenue, 2) AS product_revenue,
    ROUND(
        100.0 * revenue / (SELECT SUM(Revenue) FROM sales),
        2
    ) AS revenue_contribution_percentage
FROM product_revenue
ORDER BY revenue DESC
LIMIT 30;


-- QUERY 22: Rank products by revenue
SELECT
    StockCode,
    Description,
    ROUND(SUM(Revenue), 2) AS revenue,
    RANK() OVER (ORDER BY SUM(Revenue) DESC) AS revenue_rank
FROM sales
GROUP BY StockCode, Description
ORDER BY revenue_rank
LIMIT 30;


-- QUERY 23: High-volume products
SELECT
    StockCode,
    Description,
    SUM(Quantity) AS units_sold,
    ROUND(SUM(Revenue), 2) AS revenue,
    ROUND(
        SUM(Revenue) / NULLIF(SUM(Quantity), 0),
        2
    ) AS revenue_per_unit
FROM sales
GROUP BY StockCode, Description
HAVING SUM(Quantity) > 0
ORDER BY units_sold DESC
LIMIT 30;


-- QUERY 24: Products generating revenue in the most orders
SELECT
    StockCode,
    Description,
    COUNT(DISTINCT InvoiceNo) AS order_frequency,
    SUM(Quantity) AS units_sold,
    ROUND(SUM(Revenue), 2) AS total_revenue
FROM sales
GROUP BY StockCode, Description
ORDER BY order_frequency DESC
LIMIT 30;


-- QUERY 25: Cumulative product revenue contribution (Pareto)
WITH product_revenue AS (
    SELECT
        StockCode,
        Description,
        SUM(Revenue) AS revenue
    FROM sales
    GROUP BY StockCode, Description
),
ranked_products AS (
    SELECT
        StockCode,
        Description,
        revenue,
        RANK() OVER (ORDER BY revenue DESC) AS product_rank,
        SUM(revenue) OVER (
            ORDER BY revenue DESC, StockCode
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) AS cumulative_revenue
    FROM product_revenue
)
SELECT
    StockCode,
    Description,
    ROUND(revenue, 2) AS revenue,
    product_rank,
    ROUND(cumulative_revenue, 2) AS cumulative_revenue,
    ROUND(
        100.0 * cumulative_revenue
        / (SELECT SUM(Revenue) FROM sales),
        2
    ) AS cumulative_revenue_percentage
FROM ranked_products
ORDER BY product_rank;