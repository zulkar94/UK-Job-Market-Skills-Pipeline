"""Skill taxonomy: canonical skill name -> regex patterns that signal it in advert text.

Patterns are matched case-insensitively with word boundaries, except where a
pattern sets its own case. The "R" pattern is case-sensitive so that the
English word "r" in prose is not counted.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Skill:
    name: str
    patterns: tuple[str, ...]
    case_sensitive: bool = False


SKILLS: tuple[Skill, ...] = (
    Skill("Python", (r"python",)),
    Skill("SQL", (r"sql",)),
    Skill("R", (r"R(?![\w&])",), case_sensitive=True),
    Skill("Excel", (r"excel",)),
    Skill("Microsoft Office", (r"microsoft office", r"ms office")),
    Skill("Power BI", (r"power\s?bi",)),
    Skill("Tableau", (r"tableau",)),
    Skill("Salesforce", (r"salesforce",)),
    Skill("CRM systems", (r"crm",)),
    Skill("Stakeholder management", (r"stakeholder",)),
    Skill("Negotiation", (r"negotiat\w*",)),
    Skill("Customer service", (r"customer service", r"customer care")),
    Skill("Team leadership", (r"team leader\w*", r"line manag\w*", r"people management")),
    Skill("Rota and rostering", (r"rota", r"rostering")),
    Skill("Process improvement", (r"process improvement", r"continuous improvement", r"lean six sigma")),
    # Deliberately not "recruit\w*": "we are recruiting for" is boilerplate in many
    # adverts that have nothing to do with recruitment experience.
    Skill("Recruitment", (
        r"recruitment experience", r"recruitment consult\w*", r"recruiter",
        r"talent acquisition", r"candidate sourcing",
    )),
    Skill("Account management", (r"account manag\w*",)),
    Skill("Sales targets", (r"sales targets?", r"targets?-driven", r"quota")),
    Skill("Data analysis", (r"data analys\w*",)),
    Skill("Budget management", (r"budget\w*",)),
    Skill("Health and safety", (r"health and safety", r"h&s")),
)


def compile_skills(skills: tuple[Skill, ...] = SKILLS) -> list[tuple[str, re.Pattern[str]]]:
    """Compile every skill into one pattern per skill (patterns joined with '|')."""
    compiled = []
    for skill in skills:
        flags = 0 if skill.case_sensitive else re.IGNORECASE
        body = "|".join(f"(?:{p})" for p in skill.patterns)
        compiled.append((skill.name, re.compile(rf"(?<![\w]){body}(?![\w])", flags)))
    return compiled
