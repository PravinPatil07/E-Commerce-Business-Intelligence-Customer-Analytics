SELECT
    InvoiceYearMonth AS year_month,
    ROUND(SUM(Revenue), 2) AS monthly_revenue,
    COUNT(DISTINCT InvoiceNo) AS monthly_orders,
    COUNT(DISTINCT CustomerID) AS monthly_customers,
    SUM(Quantity) AS units_sold,
    ROUND(
        SUM(Revenue) * 1.0 / NULLIF(COUNT(DISTINCT InvoiceNo), 0),
        2
    ) AS monthly_average_order_value
FROM sales
WHERE InvoiceYearMonth IS NOT NULL
GROUP BY InvoiceYearMonth
ORDER BY InvoiceYearMonth;