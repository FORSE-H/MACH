#!/usr/bin/env python3
"""audit_licenses.py — cross-check the stated licence of every entry against the
licence the harvester independently found.

This is an AUDIT, not per-entry verification. Verification (`mach:licenseUrl` +
`mach:licenseVerified`) is a one-time human check stored on a single entry.
Auditing re-runs across the WHOLE catalogue and prints a count: where does the
hand-entered `license` field disagree with `signals.license` (harvested from the
repo / GitHub API into data/signals.json)? Run it anytime — the number comes
from code, not from memory. Its job is to catch DRIFT: a project that relicensed
upstream, or an entry we marked verified that has since gone stale.

Buckets reported:
  * CONFLICT          stated != harvested, both present  -> the real worklist
  * CONFLICT-VERIFIED a CONFLICT on a mach:licenseVerified entry (trust-critical:
                      we claimed we checked, yet the source disagrees)
  * NO-HARVEST        harvester found no licence -> no cross-check possible (gap,
                      not an error)

Exit status:
    0  no conflicts (NO-HARVEST gaps do not fail)
    1  one or more CONFLICTs (report-only callers can ignore the code)

Usage:
    python scripts/audit_licenses.py            # human-readable report
    python scripts/audit_licenses.py --json     # machine-readable, for CI later
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ENTRIES = Path("entries")
SIGNALS = Path("data/signals.json")

# Values that mean "no licence asserted" on either side. Compared case-folded.
_EMPTY = {"", "noassertion", "none", "null", "unknown", "unlicensed",
          "other", "not-open-source", "unverified", "see-license"}


def _norm(value) -> str:
    """Case-fold and trim an SPDX string so MIT == mit, map the various
    'no licence' spellings to a single empty token, and fold the deprecated /
    precision SPDX suffixes so GPL-2.0-only == GPL-2.0 == GPL-2.0-or-later-base.

    GitHub's licence detector often emits the deprecated bare id (GPL-2.0) while
    a curator writes the modern precise one (GPL-2.0-only / -or-later). Those are
    the SAME licence family, so they must not count as a conflict. We fold to the
    family stem; a genuine only-vs-or-later distinction is a licence NOTE, not a
    mismatch the harvester can ever see (it never emits the suffix)."""
    if value is None:
        return ""
    s = str(value).strip()
    if s.casefold() in _EMPTY:
        return ""
    s = s.casefold()
    # drop the deprecated/precision suffixes GitHub never emits
    for suffix in ("-or-later", "-only"):
        if s.endswith(suffix):
            s = s[: -len(suffix)]
    return s


def _load_harvested() -> dict[str, str]:
    """identifier -> harvested licence string (signals.license), or '' if none."""
    if not SIGNALS.exists():
        print(f"WARNING: {SIGNALS} not found — cannot audit. "
              f"Run the harvester / sync signals.json first.", file=sys.stderr)
        return {}
    data = json.loads(SIGNALS.read_text(encoding="utf-8"))
    out: dict[str, str] = {}
    for e in data.get("entries", []):
        ident = e.get("identifier")
        if not ident:
            continue
        out[ident] = (e.get("signals") or {}).get("license") or ""
    return out


def main(argv: list[str]) -> int:
    as_json = "--json" in argv
    harvested = _load_harvested()

    conflicts: list[dict] = []        # unresolved: stated != harvested, not reconciled
    reconciled: list[dict] = []       # verified + explained: a known, accepted discrepancy
    no_harvest: list[str] = []
    n = 0

    for f in sorted(ENTRIES.rglob("*.jsonld")):
        if f.name.startswith("_"):  # templates
            continue
        n += 1
        d = json.loads(f.read_text(encoding="utf-8"))
        ident = d.get("identifier")
        stated_raw = d.get("license", "")
        verified = bool(d.get("mach:licenseVerified"))
        has_note = bool(d.get("mach:licenseNote"))

        if ident not in harvested:
            # entry has no harvested record at all (e.g. a spec with no repo,
            # or not yet harvested) — nothing to cross-check against
            no_harvest.append(f"{ident} (no harvested record)")
            continue

        harv_raw = harvested[ident]
        if _norm(harv_raw) == "":
            no_harvest.append(f"{ident} (harvester found no licence)")
            continue

        if _norm(stated_raw) != _norm(harv_raw):
            row = {
                "identifier": ident,
                "stated": stated_raw or "<missing>",
                "harvested": harv_raw,
                "verified": verified,
                "file": str(f).replace("\\", "/"),
            }
            # A disagreement that a human has verified AND explained in a
            # licenseNote (e.g. "weights are CC-BY, the harvested MIT is the
            # code repo") is a KNOWN, accepted discrepancy — not an open
            # conflict. The harvester will disagree forever; that is expected,
            # so it must not keep sounding the alarm.
            if verified and has_note:
                reconciled.append(row)
            else:
                conflicts.append(row)

    if as_json:
        print(json.dumps({
            "entries_checked": n,
            "conflicts": conflicts,
            "reconciled": reconciled,
            "no_harvest_count": len(no_harvest),
        }, indent=2))
        return 1 if conflicts else 0

    # human-readable
    print(f"Licence audit — {n} entries checked against {SIGNALS}\n")
    print(f"  CONFLICT    {len(conflicts):>4}  stated != harvested, NOT yet reconciled  <- the worklist")
    print(f"  RECONCILED  {len(reconciled):>4}  disagrees, but human-verified + explained in a licenseNote")
    print(f"  NO-HARVEST  {len(no_harvest):>4}  no harvested licence to compare")
    print()

    if conflicts:
        print("CONFLICTS — verify these against the real LICENSE file:")
        for r in conflicts:
            flag = "!" if r["verified"] else "-"
            print(f"  {flag} {r['identifier']:<24} stated={r['stated']:<18} harvested={r['harvested']}")
        print("  (! = marked verified but has no licenseNote explaining the discrepancy)")
        print()
    else:
        print("No open licence conflicts. Every disagreement is reconciled "
              "(verified + explained) or a NO-HARVEST gap.")

    return 1 if conflicts else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
