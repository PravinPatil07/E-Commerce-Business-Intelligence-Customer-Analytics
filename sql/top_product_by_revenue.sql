SELECT
    StockCode,
    Description,
    ROUND(SUM(Revenue), 2) AS total_revenue,
    SUM(Quantity) AS total_units_sold,
    COUNT(DISTINCT InvoiceNo) AS total_orders,
    COUNT(DISTINCT CustomerID) AS total_customers,
    ROUND(
        SUM(Revenue) * 1.0 / NULLIF(SUM(Quantity), 0),
        2
    ) AS average_revenue_per_unit,
    ROUND(
        SUM(Revenue) * 1.0 / NULLIF(COUNT(DISTINCT InvoiceNo), 0),
        2
    ) AS average_order_value
FROM sales
WHERE StockCode IS NOT NULL
  AND Description IS NOT NULL
GROUP BY
    StockCode,
    Description
ORDER BY
    total_revenue DESC
LIMIT 20;