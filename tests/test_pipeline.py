"""End-to-end pipeline checks against a small fixture with hand-worked answers."""

from __future__ import annotations

import csv
import sqlite3
from pathlib import Path

import pytest

from job_market.pipeline import ANALYSIS_DIR, build_warehouse, parse_salary, read_adverts

FIELDS = [
    "advert_id",
    "title",
    "company",
    "city",
    "posted_date",
    "salary_min",
    "salary_max",
    "description",
]


def _advert(i, city, posted, description, salary=None):
    low, high = (salary, salary) if salary is not None else ("", "")
    return {
        "advert_id": f"A{i}",
        "title": "Role",
        "company": "Co",
        "city": city,
        "posted_date": posted,
        "salary_min": low,
        "salary_max": high,
        "description": description,
    }


@pytest.fixture
def warehouse(tmp_path: Path) -> sqlite3.Connection:
    rows = [
        # Six Manchester adverts that mention SQL; salaries 10k to 60k (min = max).
        *[
            _advert(i, "Manchester", "2026-01-15", "SQL and Python", salary=s * 10000)
            for i, s in enumerate(range(1, 7), start=1)
        ],
        _advert(7, "Leeds", "2026-02-03", "Excel and stakeholder management"),
        _advert(8, "Leeds", "2026-02-20", "Excel only"),
        _advert(9, "Liverpool", "2026-02-21", "Tableau and Power BI"),
    ]
    csv_path = tmp_path / "adverts.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    db_path = tmp_path / "test.db"
    build_warehouse(csv_path, db_path)
    connection = sqlite3.connect(db_path)
    yield connection
    connection.close()


def run(connection, name):
    cursor = connection.execute((ANALYSIS_DIR / name).read_text(encoding="utf-8"))
    return [c[0] for c in cursor.description], cursor.fetchall()


def test_skills_loaded_per_advert(warehouse):
    count = warehouse.execute(
        "SELECT COUNT(*) FROM advert_skills WHERE advert_id = 'A7'"
    ).fetchone()[0]
    assert count == 2  # Excel and Stakeholder management


def test_share_by_city_uses_city_total(warehouse):
    columns, rows = run(warehouse, "01_top_skills_by_city.sql")
    result = {(r[0], r[1]): r for r in rows}
    # Leeds has 2 adverts and both mention Excel, so the share is 1.0.
    assert result[("Leeds", "Excel")][2:] == (2, 2, 1.0)
    # Manchester has 6 adverts, all mentioning SQL.
    assert result[("Manchester", "SQL")][4] == 1.0


def test_skill_pairs_need_three_shared_adverts(warehouse):
    _, rows = run(warehouse, "02_skill_pairs.sql")
    assert ("Python", "SQL", 6) in rows
    assert all(count >= 3 for *_, count in rows)


def test_median_salary_handles_even_count(warehouse):
    # SQL midpoints are 10k to 60k: the median is the mean of 30k and 40k.
    _, rows = run(warehouse, "03_median_salary_by_skill.sql")
    result = {r[0]: r for r in rows}
    assert result["SQL"] == ("SQL", 6, 35000.0)
    assert "Excel" not in result  # no salary data, so it is excluded


def test_monthly_change(warehouse):
    _, rows = run(warehouse, "04_monthly_postings.sql")
    assert rows == [("2026-01", 6, None), ("2026-02", 3, -3)]


def test_read_adverts_rejects_missing_columns(tmp_path):
    bad = tmp_path / "bad.csv"
    bad.write_text("advert_id,title\n1,Role\n", encoding="utf-8")
    with pytest.raises(ValueError):
        read_adverts(bad)


def _write(path: Path, rows: list[dict], bom: bool = False) -> Path:
    with path.open("w", newline="", encoding="utf-8-sig" if bom else "utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return path


def test_excel_byte_order_mark_is_accepted(tmp_path):
    csv_path = _write(tmp_path / "bom.csv", [_advert(1, "Leeds", "2026-01-01", "SQL")], bom=True)
    assert build_warehouse(csv_path, tmp_path / "db.sqlite") == 1


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("", None),
        ("30000", 30000),
        ("30000.50", 30000),
        ("£30,000", 30000),
        (" £ 45,500 ", 45500),
    ],
)
def test_parse_salary(raw, expected):
    assert parse_salary(raw) == expected


@pytest.mark.parametrize(
    "change, message",
    [
        ({"salary_min": "40000", "salary_max": "30000"}, "below salary_min"),
        ({"salary_min": "about 30k"}, "is not a number"),
        ({"posted_date": "20/01/2026"}, "is not YYYY-MM-DD"),
        ({"advert_id": ""}, "advert_id is blank"),
    ],
)
def test_bad_rows_name_the_line(tmp_path, change, message):
    row = {**_advert(1, "Leeds", "2026-01-01", "SQL", salary=30000), **change}
    csv_path = _write(tmp_path / "bad.csv", [row])
    db_path = tmp_path / "db.sqlite"
    with pytest.raises(ValueError, match=message) as error:
        build_warehouse(csv_path, db_path)
    assert "line 2" in str(error.value)
    assert not db_path.exists()  # validation runs before the database is created


def test_duplicate_advert_id_is_rejected(tmp_path):
    rows = [_advert(1, "Leeds", "2026-01-01", "SQL"), _advert(1, "Hull", "2026-01-02", "R")]
    with pytest.raises(ValueError, match="line 3.*duplicate"):
        build_warehouse(_write(tmp_path / "dup.csv", rows), tmp_path / "db.sqlite")
