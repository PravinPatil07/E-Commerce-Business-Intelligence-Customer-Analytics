WITH country_summary AS (
    SELECT
        Country,
        ROUND(SUM(Revenue), 2) AS total_revenue,
        COUNT(DISTINCT InvoiceNo) AS total_orders,
        COUNT(DISTINCT CustomerID) AS total_customers,
        SUM(Quantity) AS total_units_sold,
        ROUND(
            SUM(Revenue) * 1.0 / NULLIF(COUNT(DISTINCT InvoiceNo), 0),
            2
        ) AS average_order_value
    FROM sales
    WHERE Country IS NOT NULL
    GROUP BY Country
),

country_metrics AS (
    SELECT
        *,
        ROUND(
            total_revenue * 100.0 /
            NULLIF(SUM(total_revenue) OVER (), 0),
            2
        ) AS revenue_percentage
    FROM country_summary
)

SELECT
    Country,
    total_revenue,
    total_orders,
    total_customers,
    total_units_sold,
    average_order_value,
    revenue_percentage
FROM country_metrics
ORDER BY total_revenue DESC;