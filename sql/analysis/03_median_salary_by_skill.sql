-- Median advertised salary midpoint for adverts that name each skill.
--
-- SQLite has no MEDIAN(), so the median is computed with ROW_NUMBER() and COUNT()
-- window functions. For an even count, the two middle rows are averaged.
-- Only adverts with both a minimum and a maximum salary are included, and skills
-- with fewer than 5 such adverts are dropped to avoid unstable medians.

WITH midpoints AS (
    SELECT
        s.skill,
        (a.salary_min + a.salary_max) / 2.0 AS midpoint
    FROM advert_skills s
    JOIN adverts a ON a.advert_id = s.advert_id
    WHERE a.salary_min IS NOT NULL
      AND a.salary_max IS NOT NULL
),
ranked AS (
    SELECT
        skill,
        midpoint,
        ROW_NUMBER() OVER (PARTITION BY skill ORDER BY midpoint) AS position,
        COUNT(*)     OVER (PARTITION BY skill)                   AS n
    FROM midpoints
)
SELECT
    skill,
    n                              AS adverts_with_salary,
    ROUND(AVG(midpoint), 0)        AS median_salary_midpoint_gbp
FROM ranked
WHERE position IN ((n + 1) / 2, (n + 2) / 2)
GROUP BY skill, n
HAVING n >= 5
ORDER BY median_salary_midpoint_gbp DESC;
