"""Generate a SYNTHETIC sample of UK job adverts for testing and demonstration.

The adverts are invented from role templates. They are not real postings, and
any findings from them describe the templates, not the UK labour market. To
analyse real demand, replace data/sample_job_adverts.csv with your own export
in the same column format.
"""

from __future__ import annotations

import argparse
import csv
import random
from datetime import date, timedelta
from pathlib import Path

# role family: (title options, skill phrases to weave into the description, salary range GBP)
ROLE_TEMPLATES: dict[str, tuple[list[str], list[str], tuple[int, int]]] = {
    "Sales": (
        ["Territory Sales Manager", "Account Executive", "Sales Representative"],
        ["sales targets", "CRM systems", "Salesforce", "account management", "negotiation", "Microsoft Office"],
        (28000, 45000),
    ),
    "Operations": (
        ["Operations Manager", "Shift Manager", "Store Operations Lead"],
        ["team leadership", "rota and rostering", "process improvement", "health and safety", "budget management", "Excel"],
        (26000, 40000),
    ),
    "Recruitment": (
        ["Recruitment Consultant", "Talent Acquisition Specialist", "Resourcer"],
        ["recruitment", "stakeholder management", "CRM systems", "negotiation"],
        (24000, 38000),
    ),
    "Data": (
        ["Data Analyst", "Business Analyst", "MI Analyst"],
        ["SQL", "Python", "Excel", "Power BI", "Tableau", "R", "data analysis", "stakeholder management"],
        (32000, 52000),
    ),
    "Public sector": (
        ["Administrative Officer", "Customer Service Advisor", "Caseworker"],
        ["customer service", "Microsoft Office", "stakeholder management", "process improvement"],
        (22000, 30000),
    ),
}

CITIES = ["Manchester", "Salford", "Liverpool", "Leeds", "London"]
PHRASE_FOR_SKILL = {
    "sales targets": "hitting sales targets",
    "CRM systems": "working in CRM systems",
    "Salesforce": "Salesforce experience",
    "account management": "account management",
    "negotiation": "strong negotiation skills",
    "Microsoft Office": "Microsoft Office proficiency",
    "team leadership": "team leadership experience",
    "rota and rostering": "rota and rostering",
    "process improvement": "process improvement",
    "health and safety": "health and safety awareness",
    "budget management": "budget management",
    "Excel": "Excel",
    "recruitment": "recruitment experience",
    "stakeholder management": "stakeholder management",
    "customer service": "a customer service focus",
    "SQL": "SQL",
    "Python": "Python",
    "Power BI": "Power BI",
    "Tableau": "Tableau",
    "R": "R",
    "data analysis": "data analysis",
}


def build_description(rng: random.Random, skills: list[str]) -> str:
    chosen = rng.sample(skills, k=min(len(skills), rng.randint(3, 5)))
    phrases = [PHRASE_FOR_SKILL[s] for s in chosen]
    if len(phrases) > 1:
        listed = ", ".join(phrases[:-1]) + " and " + phrases[-1]
    else:
        listed = phrases[0]
    return (
        f"We are recruiting for a role that needs {listed}. "
        "You will work closely with local teams and report progress weekly. "
        "Full training is provided and there is a clear route to progression."
    )


def generate(n: int, seed: int = 2026) -> list[dict]:
    rng = random.Random(seed)
    families = list(ROLE_TEMPLATES)
    start = date(2026, 1, 1)
    rows = []
    for i in range(1, n + 1):
        family = rng.choice(families)
        titles, skills, (low, high) = ROLE_TEMPLATES[family]
        salary_min = rng.randrange(low, high - 2000, 500)
        posted = start + timedelta(days=rng.randint(0, 300))
        rows.append(
            {
                "advert_id": f"SYN{i:04d}",
                "title": rng.choice(titles),
                "company": f"Synthetic Employer {rng.randint(1, 40):02d}",
                "city": rng.choice(CITIES),
                "posted_date": posted.isoformat(),
                "salary_min": salary_min if rng.random() > 0.15 else "",
                "salary_max": (salary_min + rng.randrange(3000, 8000, 500)) if rng.random() > 0.15 else "",
                "description": build_description(rng, skills),
            }
        )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n", type=int, default=240)
    parser.add_argument("--out", type=Path, default=Path("data/sample_job_adverts_SYNTHETIC.csv"))
    args = parser.parse_args()
    rows = generate(args.n)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} synthetic adverts to {args.out}")


if __name__ == "__main__":
    main()
