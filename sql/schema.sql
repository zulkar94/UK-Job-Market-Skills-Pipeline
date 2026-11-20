-- Schema for the UK job market skills warehouse (SQLite dialect).

DROP TABLE IF EXISTS advert_skills;
DROP TABLE IF EXISTS adverts;

CREATE TABLE adverts (
    advert_id    TEXT PRIMARY KEY,
    title        TEXT NOT NULL,
    company      TEXT NOT NULL,
    city         TEXT NOT NULL,
    posted_date  TEXT NOT NULL,           -- ISO 8601 (YYYY-MM-DD)
    salary_min   INTEGER,                 -- annual GBP, NULL when not advertised
    salary_max   INTEGER,
    description  TEXT NOT NULL,
    CHECK (salary_max IS NULL OR salary_min IS NULL OR salary_max >= salary_min)
);

-- One row per advert and skill mentioned in its description.
CREATE TABLE advert_skills (
    advert_id  TEXT NOT NULL REFERENCES adverts (advert_id),
    skill      TEXT NOT NULL,
    PRIMARY KEY (advert_id, skill)
);

CREATE INDEX idx_advert_skills_skill ON advert_skills (skill);
CREATE INDEX idx_adverts_city_date   ON adverts (city, posted_date);
