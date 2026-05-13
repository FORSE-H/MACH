#!/usr/bin/env python3
"""
suggest_judgement.py

Scores every entry against documented criteria and prints a comparison table
showing suggested vs current judgement. Use this to calibrate thresholds and
spot inconsistencies before publishing the criteria publicly.

Usage:
    python scripts/suggest_judgement.py
    python scripts/suggest_judgement.py --show-all          # include matching entries
    python scripts/suggest_judgement.py --show-scores       # include score breakdown
"""

import json
import argparse
from pathlib import Path

ENTRIES_DIR = Path("entries")

# ── Scoring tables ────────────────────────────────────────────────────────────

MATURITY_SCORE = {
    "production":   3,
    "beta":         2,
    "experimental": 1,
    "legacy":       0,
}

GOVERNANCE_SCORE = {
    "foundation":  3,
    "community":   3,
    "academic":    2,
    "government":  2,
    "vendor-led":  1,
    "individual":  0,
}

PERMISSIVE_LICENSES = {
    "MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause",
    "CC-BY-4.0", "CC0-1.0", "ISC", "Unlicense",
    "Public Domain",
}
COPYLEFT_LICENSES = {
    "GPL-2.0", "GPL-3.0", "LGPL-2.1", "LGPL-3.0",
    "AGPL-3.0", "MPL-2.0", "EUPL-1.2", "CC-BY-SA-4.0",
}

ACADEMIC_EVIDENCE_TYPES = {"academic-reference", "peer-reviewed"}

# ── Thresholds → judgement ────────────────────────────────────────────────────
# Max possible score = 3 (maturity) + 3 (governance) + 3 (stars)
#                    + 2 (evidence quality) + 2 (license) + 1 (evidence count)
# = 14 points

ADOPT_THRESHOLD  = 8
ASSESS_THRESHOLD = 4   # score 4–7 → Assess, below 4 → Caution


def score_entry(e: dict) -> tuple[str, dict]:
    """Return (suggested_judgement, score_breakdown)."""
    breakdown = {}

    # Maturity (0–3)
    maturity = e.get("mach:maturity", "")
    breakdown["maturity"] = MATURITY_SCORE.get(maturity, 0)

    # Governance (0–3)
    governance = e.get("mach:governance", "")
    breakdown["governance"] = GOVERNANCE_SCORE.get(governance, 0)

    # GitHub stars (0–3) — optional field mach:githubStars not yet in schema;
    # fall back to 0 if absent so the function still runs
    stars = e.get("mach:githubStars") or 0
    if stars >= 500:
        breakdown["stars"] = 3
    elif stars >= 50:
        breakdown["stars"] = 2
    elif stars > 0:
        breakdown["stars"] = 1
    else:
        breakdown["stars"] = 0

    # Evidence quality (0–2)
    evidence = e.get("mach:evidence", [])
    if isinstance(evidence, dict):
        evidence = [evidence]
    has_paper = any(
        ev.get("mach:evidenceType", "") in ACADEMIC_EVIDENCE_TYPES
        for ev in evidence
    )
    breakdown["evidence_quality"] = 2 if has_paper else 0

    # License (0–2)
    lic = e.get("license", "")
    if lic in PERMISSIVE_LICENSES:
        breakdown["license"] = 2
    elif lic in COPYLEFT_LICENSES:
        breakdown["license"] = 1
    else:
        breakdown["license"] = 0

    # Evidence count (0–1)
    breakdown["evidence_count"] = 1 if len(evidence) >= 2 else 0

    total = sum(breakdown.values())
    breakdown["total"] = total

    if total >= ADOPT_THRESHOLD:
        suggestion = "Adopt"
    elif total >= ASSESS_THRESHOLD:
        suggestion = "Assess"
    else:
        suggestion = "Caution"

    return suggestion, breakdown


def load_entries():
    entries = []
    for path in sorted(ENTRIES_DIR.rglob("*.jsonld")):
        if path.name.startswith("_"):
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            data["_path"] = str(path)
            entries.append(data)
        except json.JSONDecodeError as exc:
            print(f"WARN: skipping {path} — {exc}")
    return entries


LABEL_WIDTH = 38
JUDGEMENT_WIDTH = 12


def colour(text, judgement):
    codes = {"Adopt": "\033[32m", "Assess": "\033[33m", "Caution": "\033[31m"}
    reset = "\033[0m"
    return f"{codes.get(judgement, '')}{text}{reset}"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--show-all",    action="store_true", help="Include entries where suggestion matches current")
    parser.add_argument("--show-scores", action="store_true", help="Print score breakdown for each entry")
    args = parser.parse_args()

    entries = load_entries()
    mismatches = 0
    no_judgement = 0

    header = f"{'Entry':<{LABEL_WIDTH}} {'Current':<{JUDGEMENT_WIDTH}} {'Suggested':<{JUDGEMENT_WIDTH}} {'Score':>6}  Signals"
    print(header)
    print("-" * len(header))

    for e in entries:
        name       = e.get("name", e.get("identifier", "?"))[:LABEL_WIDTH - 1]
        current    = e.get("mach:judgement", "—")
        suggestion, breakdown = score_entry(e)
        total      = breakdown["total"]

        match = current == suggestion
        if not match and current != "—":
            mismatches += 1
        if current == "—":
            no_judgement += 1

        if not args.show_all and match:
            continue

        signals = (
            f"mat={breakdown['maturity']} "
            f"gov={breakdown['governance']} "
            f"lic={breakdown['license']} "
            f"evQ={breakdown['evidence_quality']} "
            f"evN={breakdown['evidence_count']} "
            f"str={breakdown['stars']}"
        )
        flag = "" if match else "  <--"
        print(
            f"{name:<{LABEL_WIDTH}} "
            f"{colour(current, current):<{JUDGEMENT_WIDTH + 9}} "
            f"{colour(suggestion, suggestion):<{JUDGEMENT_WIDTH + 9}} "
            f"{total:>6}  {signals}{flag}"
        )
        if args.show_scores:
            print(f"  {'':>{LABEL_WIDTH}} breakdown: {breakdown}")

    print()
    print(f"Thresholds: Adopt >= {ADOPT_THRESHOLD}  |  Assess >= {ASSESS_THRESHOLD}  |  Caution < {ASSESS_THRESHOLD}  (max 14)")
    print(f"Entries: {len(entries)} total  |  {mismatches} mismatches  |  {no_judgement} without judgement")
    if mismatches == 0 and not args.show_all:
        print("All current judgements match suggestions.")


if __name__ == "__main__":
    main()
