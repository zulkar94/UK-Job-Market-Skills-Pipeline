"""Extract canonical skills from free-text job advert descriptions."""

from __future__ import annotations

from functools import lru_cache

from .taxonomy import compile_skills


@lru_cache(maxsize=1)
def _compiled():
    return compile_skills()


def extract_skills(text: str) -> list[str]:
    """Return the canonical skills mentioned in text, in taxonomy order, without duplicates."""
    if not text:
        return []
    return [name for name, pattern in _compiled() if pattern.search(text)]
