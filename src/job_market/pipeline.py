"""Load adverts, extract skills, store them in SQLite and run the analysis queries."""

from __future__ import annotations

import argparse
import csv
import sqlite3
from pathlib import Path

from .extract import extract_skills

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "sql" / "schema.sql"
ANALYSIS_DIR = ROOT / "sql" / "analysis"

REQUIRED_COLUMNS = {"advert_id", "title", "company", "city", "posted_date", "salary_min", "salary_max", "description"}


def _optional_int(value: str) -> int | None:
    value = (value or "").strip()
    return int(float(value)) if value else None


def read_adverts(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        missing = REQUIRED_COLUMNS - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"{path} is missing columns: {sorted(missing)}")
        return list(reader)


def build_warehouse(csv_path: Path, db_path: Path) -> int:
    """Create the warehouse from a CSV of adverts. Returns the number of adverts loaded."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()
    adverts = read_adverts(csv_path)
    connection = sqlite3.connect(db_path)
    try:
        connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        for row in adverts:
            connection.execute(
                "INSERT INTO adverts VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    row["advert_id"],
                    row["title"],
                    row["company"],
                    row["city"],
                    row["posted_date"],
                    _optional_int(row["salary_min"]),
                    _optional_int(row["salary_max"]),
                    row["description"],
                ),
            )
            skills = extract_skills(row["description"])
            connection.executemany(
                "INSERT INTO advert_skills VALUES (?, ?)",
                [(row["advert_id"], skill) for skill in skills],
            )
        connection.commit()
    finally:
        connection.close()
    return len(adverts)


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
