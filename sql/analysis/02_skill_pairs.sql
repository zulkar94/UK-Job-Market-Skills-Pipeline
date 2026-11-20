-- Skills that appear together in the same advert, most frequent first.
-- A self-join on advert_skills, keeping one ordering of each pair (a.skill < b.skill).

SELECT
    a.skill AS skill_a,
    b.skill AS skill_b,
    COUNT(*) AS adverts_with_both
FROM advert_skills a
JOIN advert_skills b
    ON b.advert_id = a.advert_id
   AND b.skill > a.skill
GROUP BY a.skill, b.skill
HAVING COUNT(*) >= 3
ORDER BY adverts_with_both DESC, skill_a, skill_b;
