"""Skill extraction: positive matches and the false positives the taxonomy must avoid."""

from __future__ import annotations

import pytest

from job_market.extract import extract_skills


@pytest.mark.parametrize(
    "text, expected",
    [
        ("Experience with Python, SQL and Power BI.", ["Python", "SQL", "Power BI"]),
        ("Strong PowerBI reporting skills", ["Power BI"]),
        ("Advanced Excel and Microsoft Office", ["Excel", "Microsoft Office"]),
        (
            "Team leader for six staff who also manage rotas.",
            ["Team leadership", "Rota and rostering"],
        ),
        ("Hitting sales targets through negotiation", ["Sales targets", "Negotiation"]),
        ("Recruitment consultant with candidate sourcing", ["Recruitment"]),
    ],
)
def test_matches_expected_skills(text, expected):
    assert set(expected) <= set(extract_skills(text))


@pytest.mark.parametrize(
    "text, unexpected",
    [
        ("An excellent opportunity to grow", "Excel"),  # 'excel' inside 'excellent'
        ("Some R&D experience would help", "R"),  # R followed by &
        ("We are a clean and friendly team", "Process improvement"),
        ("Work with the r team on reports", "R"),  # lowercase r is prose, not R
        ("Good customer experience matters", "Customer service"),
        ("We are recruiting for a role in our team", "Recruitment"),  # boilerplate, not a skill
    ],
)
def test_avoids_false_positives(text, unexpected):
    assert unexpected not in extract_skills(text)


def test_r_is_detected_when_standalone():
    assert "R" in extract_skills("Skills in R, Python and SQL")


def test_empty_text_returns_no_skills():
    assert extract_skills("") == []
    assert extract_skills("No relevant keywords here.") == []


def test_no_duplicates_in_output():
    skills = extract_skills("Python python PYTHON and more Python")
    assert skills.count("Python") == 1


def test_every_synthetic_template_phrase_extracts_its_skill():
    """Keeps the synthetic data generator and the taxonomy in step."""
    from job_market.sample_data import PHRASE_FOR_SKILL

    for skill_key, phrase in PHRASE_FOR_SKILL.items():
        found = {s.lower() for s in extract_skills(phrase)}
        assert skill_key.lower() in found, f"{phrase!r} did not yield {skill_key!r}"
