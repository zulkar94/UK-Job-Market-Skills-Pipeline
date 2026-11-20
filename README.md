# UK Job Market Skills Pipeline

A pipeline that turns job adverts into a skills dataset. It extracts skills from advert text with a regex taxonomy, stores them in a SQLite warehouse, and answers four questions in plain SQL: which skills are most requested by city, which skills appear together, what the median advertised salary is for each skill, and how postings change month to month.

**The bundled dataset is synthetic.** `data/sample_job_adverts_SYNTHETIC.csv` is generated from role templates and does not describe the real UK labour market. The pipeline is complete and tested. To analyse real demand, replace the CSV with your own export in the same column format.

## Key design points

- **Taxonomy with false-positive controls.** Patterns use word boundaries, so "excellent" does not match Excel. "R" is case-sensitive and excludes "R&D". Generic words such as "recruiting" are excluded from the Recruitment skill, since they appear in boilerplate across many unrelated adverts. The test suite includes these cases.
- **Share by city uses the city total as denominator.** Raw counts would make large cities look like they need every skill.
- **Medians in SQL.** SQLite has no `MEDIAN()`, so the query uses `ROW_NUMBER()` and `COUNT()` window functions and averages the two middle rows for even counts. Skills with fewer than five salaried adverts are dropped.
- **Round-trip test.** Every phrase the synthetic generator writes must extract the skill it is meant to represent. This stops the data and the taxonomy drifting apart.

## Quick start

Requires Python 3.10+.

```bash
pip install -e ".[dev]"
python -m job_market.sample_data        # optional: regenerate the synthetic CSV
python -m job_market.pipeline           # load, extract, run SQL, write outputs/*.csv
pytest
```

To use your own data, pass the file in:

```bash
python -m job_market.pipeline --csv path/to/adverts.csv
```

Required columns: `advert_id, title, company, city, posted_date, salary_min, salary_max, description`. Dates are ISO 8601. Salaries are annual GBP, and may be blank.

## Outputs

| File | Question |
|---|---|
| `outputs/01_top_skills_by_city.csv` | Share of adverts asking for each skill, by city |
| `outputs/02_skill_pairs.csv` | Skills that appear together, with at least three shared adverts |
| `outputs/03_median_salary_by_skill.csv` | Median advertised salary midpoint, for skills with at least five salaried adverts |
| `outputs/04_monthly_postings.csv` | Adverts per month and the change from the previous month |

## Test coverage

- `tests/test_extract.py`: positive matches, false-positive exclusions, and the template round-trip.
- `tests/test_pipeline.py`: a six-advert fixture with hand-worked answers for each SQL file, including the even-count median and the first-month `NULL` in the month-on-month change.

## Limitations

- **Synthetic data.** Findings from the sample describe the templates. They should not be quoted as market evidence.
- **Keyword matching.** The taxonomy finds phrases, not meaning. It will miss skills described in unusual wording and can count a phrase used in a negative sense, such as "no Excel required".
- **Salary coverage.** Many adverts do not state a salary, so medians rest on a subset. Check `adverts_with_salary` before comparing skills.
- **Data collection.** The pipeline does not scrape job boards. Check the terms of any source before collecting adverts from it.

## Project layout

```
src/job_market/taxonomy.py      skill names and their regex patterns
src/job_market/extract.py       text to skills
src/job_market/pipeline.py      load CSV, build SQLite, run analysis
src/job_market/sample_data.py   synthetic advert generator
sql/schema.sql                  adverts and advert_skills tables
sql/analysis/*.sql              four analysis queries
tests/                          pytest suite
outputs/                        generated CSV results
```

## Licence

MIT. See [LICENSE](LICENSE).
