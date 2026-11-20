-- Adverts posted per month, with the month-on-month change.

WITH monthly AS (
    SELECT
        STRFTIME('%Y-%m', posted_date) AS month,
        COUNT(*)                       AS adverts
    FROM adverts
    GROUP BY month
)
SELECT
    month,
    adverts,
    adverts - LAG(adverts) OVER (ORDER BY month) AS change_from_previous_month
FROM monthly
ORDER BY month;
