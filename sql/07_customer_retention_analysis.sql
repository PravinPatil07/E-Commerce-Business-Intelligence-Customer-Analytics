-- =============================================================================
-- FILE: 07_customer_retention_analysis.sql
-- CUSTOMER RETENTION & COHORT ANALYSIS
-- =============================================================================

-- QUERY 39: Customer first purchase month
WITH customer_first_purchase AS (
    SELECT
        CustomerID,
        MIN(date(InvoiceDate)) AS first_purchase_date
    FROM customer_sales
    GROUP BY CustomerID
)
SELECT
    CustomerID,
    first_purchase_date,
    strftime('%Y-%m', first_purchase_date) AS cohort_month
FROM customer_first_purchase
ORDER BY cohort_month, CustomerID;


-- QUERY 40: Customer cohort monthly activity
WITH first_purchase AS (
    SELECT
        CustomerID,
        MIN(date(InvoiceDate)) AS first_purchase_date
    FROM customer_sales
    GROUP BY CustomerID
),
cohorts AS (
    SELECT
        CustomerID,
        strftime('%Y-%m', first_purchase_date) AS cohort_month
    FROM first_purchase
),
monthly_activity AS (
    SELECT DISTINCT
        CustomerID,
        strftime('%Y-%m', InvoiceDate) AS activity_month
    FROM customer_sales
)
SELECT
    c.cohort_month,
    a.activity_month,
    COUNT(DISTINCT a.CustomerID) AS active_customers
FROM cohorts c
JOIN monthly_activity a
    ON c.CustomerID = a.CustomerID
GROUP BY c.cohort_month, a.activity_month
ORDER BY c.cohort_month, a.activity_month;


-- QUERY 41: Cohort month index
WITH first_purchase AS (
    SELECT
        CustomerID,
        MIN(date(InvoiceDate)) AS first_purchase_date
    FROM customer_sales
    GROUP BY CustomerID
),
customer_cohort AS (
    SELECT
        CustomerID,
        CAST(strftime('%Y', first_purchase_date) AS INTEGER) AS cohort_year,
        CAST(strftime('%m', first_purchase_date) AS INTEGER) AS cohort_month
    FROM first_purchase
),
monthly_activity AS (
    SELECT DISTINCT
        CustomerID,
        CAST(strftime('%Y', InvoiceDate) AS INTEGER) AS activity_year,
        CAST(strftime('%m', InvoiceDate) AS INTEGER) AS activity_month
    FROM customer_sales
)
SELECT
    c.cohort_year,
    c.cohort_month,
    a.activity_year,
    a.activity_month,
    (
        (a.activity_year - c.cohort_year) * 12
        + (a.activity_month - c.cohort_month)
    ) AS cohort_month_index,
    COUNT(DISTINCT a.CustomerID) AS active_customers
FROM customer_cohort c
JOIN monthly_activity a
    ON c.CustomerID = a.CustomerID
GROUP BY
    c.cohort_year,
    c.cohort_month,
    a.activity_year,
    a.activity_month
ORDER BY
    c.cohort_year,
    c.cohort_month,
    cohort_month_index;


-- QUERY 42: Cohort retention percentages
WITH first_purchase AS (
    SELECT
        CustomerID,
        MIN(date(InvoiceDate)) AS first_purchase_date
    FROM customer_sales
    GROUP BY CustomerID
),
cohort AS (
    SELECT
        CustomerID,
        strftime('%Y-%m', first_purchase_date) AS cohort_month,
        CAST(strftime('%Y', first_purchase_date) AS INTEGER) AS cohort_year,
        CAST(strftime('%m', first_purchase_date) AS INTEGER) AS cohort_month_number
    FROM first_purchase
),
activity AS (
    SELECT DISTINCT
        CustomerID,
        CAST(strftime('%Y', InvoiceDate) AS INTEGER) AS activity_year,
        CAST(strftime('%m', InvoiceDate) AS INTEGER) AS activity_month
    FROM customer_sales
),
cohort_activity AS (
    SELECT
        c.cohort_month,
        c.cohort_year,
        c.cohort_month_number,
        (
            (a.activity_year - c.cohort_year) * 12
            + (a.activity_month - c.cohort_month_number)
        ) AS month_index,
        COUNT(DISTINCT a.CustomerID) AS retained_customers
    FROM cohort c
    JOIN activity a
        ON c.CustomerID = a.CustomerID
    GROUP BY
        c.cohort_month,
        c.cohort_year,
        c.cohort_month_number,
        month_index
),
cohort_sizes AS (
    SELECT
        cohort_month,
        COUNT(DISTINCT CustomerID) AS cohort_size
    FROM cohort
    GROUP BY cohort_month
)
SELECT
    ca.cohort_month,
    ca.month_index,
    cs.cohort_size,
    ca.retained_customers,
    ROUND(
        100.0 * ca.retained_customers / cs.cohort_size,
        2
    ) AS retention_percentage
FROM cohort_activity ca
JOIN cohort_sizes cs
    ON ca.cohort_month = cs.cohort_month
ORDER BY ca.cohort_month, ca.month_index;


-- QUERY 43: Repeat customer percentage by month
WITH monthly_customer_orders AS (
    SELECT
        strftime('%Y-%m', InvoiceDate) AS year_month,
        CustomerID,
        COUNT(DISTINCT InvoiceNo) AS monthly_orders
    FROM customer_sales
    GROUP BY year_month, CustomerID
)
SELECT
    year_month,
    COUNT(*) AS monthly_customers,
    SUM(CASE WHEN monthly_orders > 1 THEN 1 ELSE 0 END)
        AS repeat_buyers_within_month,
    ROUND(
        100.0 * SUM(CASE WHEN monthly_orders > 1 THEN 1 ELSE 0 END)
        / COUNT(*),
        2
    ) AS repeat_buyer_percentage
FROM monthly_customer_orders
GROUP BY year_month
ORDER BY year_month;


-- QUERY 44: New vs returning customers by month
WITH customer_first_order AS (
    SELECT
        CustomerID,
        MIN(date(InvoiceDate)) AS first_purchase_date
    FROM customer_sales
    GROUP BY CustomerID
),
monthly_customer_activity AS (
    SELECT DISTINCT
        CustomerID,
        strftime('%Y-%m', InvoiceDate) AS year_month
    FROM customer_sales
)
SELECT
    a.year_month,
    COUNT(DISTINCT CASE
        WHEN strftime('%Y-%m', f.first_purchase_date) = a.year_month
        THEN a.CustomerID
    END) AS new_customers,
    COUNT(DISTINCT CASE
        WHEN strftime('%Y-%m', f.first_purchase_date) < a.year_month
        THEN a.CustomerID
    END) AS returning_customers
FROM monthly_customer_activity a
JOIN customer_first_order f
    ON a.CustomerID = f.CustomerID
GROUP BY a.year_month
ORDER BY a.year_month;