#!/usr/bin/env python3
"""check_entry_leaks.py — catch copy-paste leaks between entries.

New entries are often created by cloning an existing entry's JSON-LD and editing
the obvious fields. The failure mode is forgetting a field, so the new entry
still carries *another* entry's identity — the exact bug that put TxAgent's
project page in ToolUniverse's `url`, and a path to the TxAgent entry in its
`relatedLink`.

This linter flags the clearest signature of that mistake: a `relatedLink` that
points at a *different* entry's own folder (`entries/<cat>/<other-id>`). That is
almost never intentional — cross-references between entries belong in prose or in
a real external URL, not as a link to another entry's source path — so it is a
hard CI gate with near-zero false positives.

It deliberately does NOT flag url/homepage domain mismatches: a project's site
and its docs/repo legitimately live on different domains (monai.io vs
project-monai.github.io), so that check is noisy and belongs in a report a human
eyeballs, not a build gate.

Usage:
    python scripts/check_entry_leaks.py        # exit 1 if any leak is found
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ENTRIES = Path("entries")

# entries/<category>/<id>  — the internal source path of another entry
_ENTRY_PATH = re.compile(r"entries/[a-z0-9-]+/([a-z0-9][a-z0-9._-]*)")


def _listify(v) -> list:
    return v if isinstance(v, list) else ([v] if v else [])


def main() -> int:
    ids: dict[str, Path] = {}
    entries: list[tuple[str, Path, dict]] = []
    for f in sorted(ENTRIES.rglob("*.jsonld")):
        if f.name.startswith("_"):
            continue
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except ValueError as exc:
            print(f"ERROR: {f}: invalid JSON ({exc})")
            return 1
        ident = d.get("identifier")
        if ident:
            ids[ident] = f
            entries.append((ident, f, d))

    errors: list[str] = []
    for ident, f, d in entries:
        # A relatedLink that points at ANOTHER entry's folder path.
        for link in _listify(d.get("relatedLink")):
            m = _ENTRY_PATH.search(str(link))
            if m and m.group(1) != ident:
                target = m.group(1)
                where = "a real entry" if target in ids else "an entry path"
                errors.append(
                    f"{f}: relatedLink points to {where} other than itself "
                    f"('{target}') — likely a leftover from cloning that entry. "
                    f"Use an external URL or remove it."
                )

    if errors:
        print(f"Found {len(errors)} cross-entry leak(s):\n")
        for e in errors:
            print(f"ERROR: {e}")
        return 1

    print(f"No cross-entry leaks — {len(entries)} entries checked.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
