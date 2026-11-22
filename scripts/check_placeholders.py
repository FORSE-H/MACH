#!/usr/bin/env python3
"""check_placeholders.py — reject entries that still carry template placeholders.

Every category has an `entries/<cat>/_template.jsonld` to clone. The point of a
template is a safe starting skeleton, but only if forgetting to fill a field
fails loudly. This linter scans every real entry (the `_`-prefixed templates are
skipped) for the tell-tale placeholder strings and fails the build if any remain,
so a half-filled clone can never merge.

Usage:
    python scripts/check_placeholders.py      # exit 1 if any placeholder remains
"""

from __future__ import annotations

from pathlib import Path

ENTRIES = Path("entries")

# Strings that only ever appear in an unfilled template. Kept literal and
# specific so they never match legitimate content.
PLACEHOLDERS = [
    "REPLACE-WITH-SLUG",
    "REPLACE-with-the-",
    "REPLACE-keywords",
    "REPLACE-source-page",
    "REPLACE-spec-page",
    "REPLACE-catalog-page",
    "REPLACE-licence-page",
    "doi.org/REPLACE",
    "SPDX-EXPRESSION-HERE",
    "YYYY-MM-DD",
    "Organisation Name",
    "Standards Body Name",
    "Lab / Organisation Name",
    "Project Name",
    "Model Name",
    "Tool Name",
    "Dataset / Benchmark Name",
    "Data Source Name",
    "Standard / Specification Name",
    "Hardware / Device Design Name",
    "Catalog / Registry Name",
    "https://org-site",
    "https://github.com/org/repo",
    "Remove this _comment before committing",
]


def main() -> int:
    errors: list[str] = []
    n = 0
    for f in sorted(ENTRIES.rglob("*.jsonld")):
        if f.name.startswith("_"):  # the templates themselves — skip
            continue
        n += 1
        text = f.read_text(encoding="utf-8")
        hits = [p for p in PLACEHOLDERS if p in text]
        if hits:
            errors.append(f"{f}: unfilled template placeholder(s): {', '.join(hits)}")

    if errors:
        print(f"Found {len(errors)} entr{'y' if len(errors) == 1 else 'ies'} with template placeholders:\n")
        for e in errors:
            print(f"ERROR: {e}")
        print("\nFill every placeholder from the real source before committing.")
        return 1

    print(f"No template placeholders — {n} entries checked.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
