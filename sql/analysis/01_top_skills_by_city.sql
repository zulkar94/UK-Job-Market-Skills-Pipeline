-- Share of adverts asking for each skill, by city.
-- The denominator is every advert in the city, so skills are comparable across cities.

WITH city_totals AS (
    SELECT city, COUNT(*) AS adverts
    FROM adverts
    GROUP BY city
)
SELECT
    a.city,
    s.skill,
    COUNT(DISTINCT s.advert_id)                                   AS adverts_with_skill,
    t.adverts                                                     AS city_adverts,
    ROUND(1.0 * COUNT(DISTINCT s.advert_id) / t.adverts, 3)       AS share_of_adverts
FROM advert_skills s
JOIN adverts a       ON a.advert_id = s.advert_id
JOIN city_totals t   ON t.city = a.city
GROUP BY a.city, s.skill
ORDER BY a.city, share_of_adverts DESC, s.skill;
