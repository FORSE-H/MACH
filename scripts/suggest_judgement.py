#!/usr/bin/env python3
"""
suggest_judgement.py

Scores every entry against documented criteria and prints a comparison table
showing suggested vs current judgement. Use this to calibrate thresholds and
spot inconsistencies before publishing the criteria publicly.

Signals (max 16 pts):
  maturity       0-3   production=3, beta=2, experimental=1, legacy=0
  governance     0-3   foundation/community=3, academic/gov=2, vendor=1, individual=0
  forks          0-2   100+=2, 20+=1  (better institutional proxy than stars)
  pypi_downloads 0-2   50k+/mo=2, 5k+/mo=1  (0 if not on PyPI — not a penalty)
  stars          0-1   500+=1  (tiebreaker only — downweighted for healthcare context)
  evidence_qual  0-2   peer-reviewed paper=2
  license        0-2   permissive=2, copyleft=1
  evidence_count 0-1   2+ evidence items=1

Thresholds:  Adopt >= 9  |  Assess >= 5  |  Caution < 5

Usage:
    python scripts/suggest_judgement.py
    python scripts/suggest_judgement.py --show-all       # include matching entries
    python scripts/suggest_judgement.py --show-scores    # print score breakdown
    python scripts/suggest_judgement.py --no-fetch       # skip all API calls (offline)
    python scripts/suggest_judgement.py --refresh-cache  # delete cache and re-fetch

Set GITHUB_TOKEN env var to raise GitHub rate limit from 60 to 5000 req/hr.
"""

import json
import argparse
import os
import urllib.request
import urllib.error
from pathlib import Path

ENTRIES_DIR = Path("entries")
_CACHE_FILE  = Path(".mach_cache.json")

# ── Cache: { "gh:<url>": {"stars": N, "forks": N}, "pypi:<pkg>": N } ─────────

_cache: dict = {}
_gh_rate_limited = False


def _load_cache():
    if _CACHE_FILE.exists():
        try:
            _cache.update(json.loads(_CACHE_FILE.read_text(encoding="utf-8")))
        except Exception:
            pass


def _save_cache():
    _CACHE_FILE.write_text(json.dumps(_cache, indent=2), encoding="utf-8")


# ── GitHub fetcher (stars + forks in one call) ────────────────────────────────

def _gh_headers() -> dict:
    h = {"User-Agent": "MACH-catalog"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


def fetch_github(repo_url: str) -> dict:
    """Return {"stars": N, "forks": N}. Cached. 0s on any error."""
    global _gh_rate_limited
    empty = {"stars": 0, "forks": 0}
    if not repo_url or "github.com" not in repo_url:
        return empty

    key = f"gh:{repo_url}"
    if key in _cache:
        return _cache[key]
    if _gh_rate_limited:
        return empty

    path = repo_url.rstrip("/").replace(".git", "")
    parts = path.split("github.com/")[-1].split("/")
    if len(parts) < 2:
        return empty
    owner, repo = parts[0], parts[1]

    try:
        req = urllib.request.Request(
            f"https://api.github.com/repos/{owner}/{repo}",
            headers=_gh_headers()
        )
        with urllib.request.urlopen(req, timeout=6) as resp:
            data = json.loads(resp.read())
            result = {
                "stars": data.get("stargazers_count", 0),
                "forks": data.get("forks_count", 0),
            }
    except urllib.error.HTTPError as e:
        if e.code in (403, 429):
            _gh_rate_limited = True
            print("  WARNING: GitHub rate limit hit — set GITHUB_TOKEN for 5000 req/hr")
        result = empty
    except Exception:
        result = empty

    _cache[key] = result
    _save_cache()
    return result


# ── PyPI fetcher (monthly downloads via pypistats.org) ───────────────────────

def _guess_pypi_name(e: dict) -> list[str]:
    """Return candidate PyPI package names to try, in priority order."""
    candidates = []
    identifier = e.get("identifier", "")
    name = e.get("name", "")
    if identifier:
        candidates.append(identifier.lower())
    if name:
        candidates.append(name.lower().replace(" ", "-"))
        candidates.append(name.lower().replace(" ", "_"))
    return list(dict.fromkeys(candidates))  # deduplicate, preserve order


def fetch_pypi_downloads(e: dict) -> int:
    """Return last-month PyPI downloads, 0 if package not found. Cached."""
    for pkg in _guess_pypi_name(e):
        key = f"pypi:{pkg}"
        if key in _cache:
            return _cache[key]

        try:
            req = urllib.request.Request(
                f"https://pypistats.org/api/packages/{pkg}/recent",
                headers={"User-Agent": "MACH-catalog"}
            )
            with urllib.request.urlopen(req, timeout=6) as resp:
                data = json.loads(resp.read())
                downloads = data.get("data", {}).get("last_month", 0)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                _cache[key] = 0
                _save_cache()
                continue  # try next candidate name
            downloads = 0
        except Exception:
            downloads = 0

        _cache[key] = downloads
        _save_cache()
        return downloads

    return 0


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
    "CC-BY-4.0", "CC0-1.0", "ISC", "Unlicense", "Public Domain",
}
COPYLEFT_LICENSES = {
    "GPL-2.0", "GPL-3.0", "LGPL-2.1", "LGPL-3.0",
    "AGPL-3.0", "MPL-2.0", "EUPL-1.2", "CC-BY-SA-4.0",
}

ACADEMIC_EVIDENCE_TYPES = {"academic-reference", "peer-reviewed"}

ADOPT_THRESHOLD  = 9
ASSESS_THRESHOLD = 5   # 5–8 → Assess, <5 → Caution


def score_entry(e: dict, do_fetch: bool = True) -> tuple[str, dict]:
    """Return (suggested_judgement, score_breakdown)."""
    bd = {}

    # Maturity (0-3)
    bd["maturity"] = MATURITY_SCORE.get(e.get("mach:maturity", ""), 0)

    # Governance (0-3)
    bd["governance"] = GOVERNANCE_SCORE.get(e.get("mach:governance", ""), 0)

    # GitHub forks (0-2) — institutional adoption proxy
    # GitHub stars (0-1) — tiebreaker only
    repo_url = e.get("codeRepository", "") or e.get("url", "")
    if do_fetch:
        gh = fetch_github(repo_url)
    else:
        gh = {"stars": 0, "forks": 0}

    forks = gh["forks"]
    stars = gh["stars"]

    bd["forks"]      = 2 if forks >= 100 else (1 if forks >= 20 else 0)
    bd["forks_raw"]  = forks
    bd["stars"]      = 1 if stars >= 500 else 0
    bd["stars_raw"]  = stars

    # PyPI monthly downloads (0-2) — 0 if not on PyPI, not a penalty
    if do_fetch:
        pypi = fetch_pypi_downloads(e)
    else:
        pypi = 0
    bd["pypi"]     = 2 if pypi >= 50_000 else (1 if pypi >= 5_000 else 0)
    bd["pypi_raw"] = pypi

    # Evidence quality (0-2)
    evidence = e.get("mach:evidence", [])
    if isinstance(evidence, dict):
        evidence = [evidence]
    has_paper = any(
        ev.get("mach:evidenceType", "") in ACADEMIC_EVIDENCE_TYPES
        for ev in evidence
    )
    bd["evidence_qual"]  = 2 if has_paper else 0
    bd["evidence_count"] = 1 if len(evidence) >= 2 else 0

    # License (0-2)
    lic = e.get("license", "")
    bd["license"] = 2 if lic in PERMISSIVE_LICENSES else (1 if lic in COPYLEFT_LICENSES else 0)

    _raw_keys = {"forks_raw", "stars_raw", "pypi_raw"}
    total = sum(v for k, v in bd.items() if k not in _raw_keys)
    bd["total"] = total

    if total >= ADOPT_THRESHOLD:
        suggestion = "Adopt"
    elif total >= ASSESS_THRESHOLD:
        suggestion = "Assess"
    else:
        suggestion = "Caution"

    return suggestion, bd


# ── Output helpers ────────────────────────────────────────────────────────────

LABEL_WIDTH    = 38
JUDGEMENT_WIDTH = 12


def colour(text, judgement):
    codes = {"Adopt": "\033[32m", "Assess": "\033[33m", "Caution": "\033[31m"}
    return f"{codes.get(judgement, '')}{text}\033[0m"


def fmt_raw(score, raw) -> str:
    return f"{score}({raw})" if raw else str(score)


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


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--show-all",      action="store_true", help="Include entries where suggestion matches current")
    parser.add_argument("--show-scores",   action="store_true", help="Print full score breakdown per entry")
    parser.add_argument("--no-fetch",      action="store_true", help="Skip all API calls (offline mode)")
    parser.add_argument("--refresh-cache", action="store_true", help="Delete cache and re-fetch everything")
    args = parser.parse_args()

    do_fetch = not args.no_fetch

    if args.refresh_cache and _CACHE_FILE.exists():
        _CACHE_FILE.unlink()
        print(f"Cache cleared: {_CACHE_FILE}\n")

    if do_fetch:
        _load_cache()
        cached = len(_cache)
        token_hint = " (GITHUB_TOKEN set)" if os.environ.get("GITHUB_TOKEN") else " (set GITHUB_TOKEN for 5000 req/hr)"
        hint = f"  {cached} entries cached" if cached else token_hint
        print(f"Fetching GitHub + PyPI data...{hint}\n")

    entries = load_entries()
    mismatches = 0
    no_judgement = 0

    header = (
        f"{'Entry':<{LABEL_WIDTH}} "
        f"{'Current':<{JUDGEMENT_WIDTH}} "
        f"{'Suggested':<{JUDGEMENT_WIDTH}} "
        f"{'Pts':>4}  Signals"
    )
    print(header)
    print("-" * (len(header) + 20))

    for e in entries:
        name       = e.get("name", e.get("identifier", "?"))[:LABEL_WIDTH - 1]
        current    = e.get("mach:judgement", "-")
        suggestion, bd = score_entry(e, do_fetch=do_fetch)
        total      = bd["total"]

        match = current == suggestion
        if not match and current != "-":
            mismatches += 1
        if current == "-":
            no_judgement += 1

        if not args.show_all and match:
            continue

        signals = (
            f"mat={bd['maturity']} "
            f"gov={bd['governance']} "
            f"frk={fmt_raw(bd['forks'], bd['forks_raw'])} "
            f"pypi={fmt_raw(bd['pypi'], bd['pypi_raw'])} "
            f"str={fmt_raw(bd['stars'], bd['stars_raw'])} "
            f"evQ={bd['evidence_qual']} "
            f"lic={bd['license']} "
            f"evN={bd['evidence_count']}"
        )
        flag = "" if match else "  <--"
        print(
            f"{name:<{LABEL_WIDTH}} "
            f"{colour(current, current):<{JUDGEMENT_WIDTH + 9}} "
            f"{colour(suggestion, suggestion):<{JUDGEMENT_WIDTH + 9}} "
            f"{total:>4}  {signals}{flag}"
        )
        if args.show_scores:
            print(f"  {'':>{LABEL_WIDTH}} {bd}")

    print()
    print(
        f"Signals: maturity(3) governance(3) forks(2) pypi(2) stars(1) "
        f"evidence_quality(2) license(2) evidence_count(1) = 16 max"
    )
    print(f"Thresholds: Adopt >= {ADOPT_THRESHOLD}  |  Assess >= {ASSESS_THRESHOLD}  |  Caution < {ASSESS_THRESHOLD}")
    print(f"Entries: {len(entries)} total  |  {mismatches} mismatches  |  {no_judgement} without judgement")
    if mismatches == 0 and not args.show_all:
        print("All current judgements match suggestions.")


if __name__ == "__main__":
    main()
