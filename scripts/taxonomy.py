#!/usr/bin/env python3
"""
taxonomy.py
Single source of truth for MACH taxonomy lookups.
Reads data/taxonomy/categories.yaml — all scripts should import from here
rather than maintaining their own hardcoded dicts.
"""

from pathlib import Path
import yaml

_TAXONOMY_PATH = Path(__file__).parent.parent / "data" / "taxonomy" / "categories.yaml"
_taxonomy = None


def _load():
    global _taxonomy
    if _taxonomy is None:
        _taxonomy = yaml.safe_load(_TAXONOMY_PATH.read_text(encoding="utf-8"))
    return _taxonomy


def category_labels() -> dict[str, str]:
    """Return {slug: display_name} for all 14 categories."""
    return {c["id"]: c["name"] for c in _load()["categories"]}


def category_ids() -> list[str]:
    """Return ordered list of all category slugs."""
    return [c["id"] for c in _load()["categories"]]


def judgement_ids() -> list[str]:
    """Return valid judgement values: Adopt, Situational, Assess, Caution."""
    return [j["id"] for j in _load()["judgements"]]


def maturity_levels() -> list[str]:
    return _load()["maturity_levels"]


def governance_types() -> list[str]:
    return _load()["governance_types"]


def label(category_slug: str) -> str:
    """Return display name for a category slug, or the slug itself if not found."""
    return category_labels().get(category_slug, category_slug)
