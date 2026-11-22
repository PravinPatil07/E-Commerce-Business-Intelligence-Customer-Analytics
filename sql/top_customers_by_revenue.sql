SELECT
    CustomerID,
    ROUND(SUM(Revenue), 2) AS total_revenue,
    COUNT(DISTINCT InvoiceNo) AS total_orders,
    SUM(Quantity) AS total_units_sold,
    ROUND(
        SUM(Revenue) * 1.0 / NULLIF(COUNT(DISTINCT InvoiceNo), 0),
        2
    ) AS average_order_value,
    MIN(date(InvoiceDate)) AS first_purchase_date,
    MAX(date(InvoiceDate)) AS last_purchase_date
FROM sales
WHERE CustomerID IS NOT NULL
GROUP BY CustomerID
ORDER BY total_revenue DESC
LIMIT 20;