"""Load adverts, extract skills, store them in SQLite and run the analysis queries."""

from __future__ import annotations

import argparse
import csv
import sqlite3
from datetime import date
from pathlib import Path

from .extract import extract_skills

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "sql" / "schema.sql"
ANALYSIS_DIR = ROOT / "sql" / "analysis"

REQUIRED_COLUMNS = {
    "advert_id",
    "title",
    "company",
    "city",
    "posted_date",
    "salary_min",
    "salary_max",
    "description",
}


def parse_salary(value: str) -> int | None:
    """Parse an annual salary such as '30000', '30000.50' or '£30,000'. Blank means None."""
    cleaned = (value or "").replace("£", "").replace(",", "").strip()
    if not cleaned:
        return None
    return int(float(cleaned))


def read_adverts(path: Path) -> list[dict]:
    # utf-8-sig strips the byte-order mark that Excel adds to exported CSV files.
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        missing = REQUIRED_COLUMNS - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"{path} is missing columns: {sorted(missing)}")
        return list(reader)


def validate_adverts(adverts: list[dict]) -> list[tuple]:
    """Check every row and return insert-ready tuples.

    Errors name the CSV line and advert_id, and are raised before the database
    is touched, so a bad file never leaves a half-built warehouse behind.
    """
    seen: set[str] = set()
    rows = []
    for line, row in enumerate(adverts, start=2):  # line 1 is the header
        advert_id = (row["advert_id"] or "").strip()
        where = f"line {line} (advert_id {advert_id!r})"
        if not advert_id:
            raise ValueError(f"line {line}: advert_id is blank")
        if advert_id in seen:
            raise ValueError(f"{where}: duplicate advert_id")
        seen.add(advert_id)
        try:
            date.fromisoformat(row["posted_date"].strip())
        except ValueError:
            raise ValueError(
                f"{where}: posted_date {row['posted_date']!r} is not YYYY-MM-DD"
            ) from None
        try:
            salary_min = parse_salary(row["salary_min"])
            salary_max = parse_salary(row["salary_max"])
        except ValueError:
            raise ValueError(
                f"{where}: salary {row['salary_min']!r} to {row['salary_max']!r} is not a number"
            ) from None
        if salary_min is not None and salary_max is not None and salary_max < salary_min:
            raise ValueError(f"{where}: salary_max {salary_max} is below salary_min {salary_min}")
        rows.append(
            (
                advert_id,
                row["title"],
                row["company"],
                row["city"],
                row["posted_date"].strip(),
                salary_min,
                salary_max,
                row["description"],
            )
        )
    return rows


def build_warehouse(csv_path: Path, db_path: Path) -> int:
    """Create the warehouse from a CSV of adverts. Returns the number of adverts loaded."""
    rows = validate_adverts(read_adverts(csv_path))
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()
    connection = sqlite3.connect(db_path)
    try:
        connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        connection.executemany("INSERT INTO adverts VALUES (?, ?, ?, ?, ?, ?, ?, ?)", rows)
        connection.executemany(
            "INSERT INTO advert_skills VALUES (?, ?)",
            [(row[0], skill) for row in rows for skill in extract_skills(row[7])],
        )
        connection.commit()
    finally:
        connection.close()
    return len(rows)


def run_analysis(db_path: Path, out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    connection = sqlite3.connect(db_path)
    try:
        for sql_path in sorted(ANALYSIS_DIR.glob("*.sql")):
            cursor = connection.execute(sql_path.read_text(encoding="utf-8"))
            columns = [c[0] for c in cursor.description]
            target = out_dir / f"{sql_path.stem}.csv"
            with target.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.writer(handle)
                writer.writerow(columns)
                writer.writerows(cursor.fetchall())
            written.append(target)
    finally:
        connection.close()
    return written


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, default=Path("data/sample_job_adverts_SYNTHETIC.csv"))
    parser.add_argument("--db", type=Path, default=Path("data/job_market.db"))
    parser.add_argument("--out", type=Path, default=Path("outputs"))
    args = parser.parse_args()
    count = build_warehouse(args.csv, args.db)
    print(f"Loaded {count} adverts into {args.db}")
    for path in run_analysis(args.db, args.out):
        print(f"Wrote {path}")


if __name__ == "__main__":
    main()
