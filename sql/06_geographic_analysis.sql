-- =============================================================================
-- FILE: 06_geographic_analysis.sql
-- GEOGRAPHIC ANALYSIS
-- =============================================================================

-- QUERY 33: Country performance overview
SELECT
    Country,
    ROUND(SUM(Revenue), 2) AS total_revenue,
    COUNT(DISTINCT InvoiceNo) AS total_orders,
    COUNT(DISTINCT CustomerID) AS identifiable_customers,
    SUM(Quantity) AS units_sold,
    ROUND(
        SUM(Revenue) / NULLIF(COUNT(DISTINCT InvoiceNo), 0),
        2
    ) AS average_order_value
FROM sales
GROUP BY Country
ORDER BY total_revenue DESC;


-- QUERY 34: Country revenue ranking
SELECT
    Country,
    ROUND(SUM(Revenue), 2) AS revenue,
    RANK() OVER (ORDER BY SUM(Revenue) DESC) AS country_rank
FROM sales
GROUP BY Country
ORDER BY country_rank;


-- QUERY 35: Country revenue contribution
WITH country_revenue AS (
    SELECT
        Country,
        SUM(Revenue) AS revenue
    FROM sales
    GROUP BY Country
)
SELECT
    Country,
    ROUND(revenue, 2) AS revenue,
    ROUND(
        100.0 * revenue / (SELECT SUM(Revenue) FROM sales),
        2
    ) AS revenue_contribution_percentage
FROM country_revenue
ORDER BY revenue DESC;


-- QUERY 36: Revenue per identifiable customer by country
SELECT
    Country,
    ROUND(SUM(Revenue), 2) AS revenue,
    COUNT(DISTINCT CustomerID) AS customers,
    COUNT(DISTINCT InvoiceNo) AS orders,
    ROUND(
        SUM(Revenue) / NULLIF(COUNT(DISTINCT CustomerID), 0),
        2
    ) AS revenue_per_identifiable_customer
FROM sales
GROUP BY Country
HAVING COUNT(DISTINCT CustomerID) > 0
ORDER BY revenue_per_identifiable_customer DESC;


-- QUERY 37: Top 10 countries by order volume
SELECT
    Country,
    COUNT(DISTINCT InvoiceNo) AS orders,
    ROUND(SUM(Revenue), 2) AS revenue,
    COUNT(DISTINCT CustomerID) AS customers
FROM sales
GROUP BY Country
ORDER BY orders DESC
LIMIT 10;


-- QUERY 38: Country monthly trend
SELECT
    Country,
    strftime('%Y-%m', InvoiceDate) AS year_month,
    ROUND(SUM(Revenue), 2) AS monthly_revenue,
    COUNT(DISTINCT InvoiceNo) AS monthly_orders
FROM sales
GROUP BY Country, year_month
ORDER BY Country, year_month;