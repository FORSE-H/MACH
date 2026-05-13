#!/usr/bin/env python3
"""
suggest_judgement.py

Scores every entry against two independent criteria sets and prints a comparison
table showing suggested vs current judgement.

── Editorial score (max 16 pts) ──────────────────────────────────────────────
  maturity       0-3   production=3, beta=2, experimental=1, legacy=0
  governance     0-3   foundation/community=3, academic/gov=2, vendor=1, individual=0
  forks          0-2   100+=2, 20+=1  (better institutional proxy than stars)
  pypi_downloads 0-2   50k+/mo=2, 5k+/mo=1  (0 if not on PyPI — not a penalty)
  stars          0-1   500+=1  (tiebreaker only — downweighted for healthcare context)
  evidence_qual  0-2   peer-reviewed paper=2
  license        0-2   permissive=2, copyleft=1
  evidence_count 0-1   2+ evidence items=1

  Thresholds:  Adopt >= 9  |  Assess >= 5  |  Caution < 5

── FAIR score (max 8 pts, per FAIRsoft/howfairis) ────────────────────────────
  F1  0-1   unique identity  (identifier + @id both present)
  F2  0-1   community registry  (found on PyPI)
  A1  0-1   accessible repo  (codeRepository on known host)
  A2  0-1   versioned  (softwareVersion or dateModified present)
  I1  0-1   open health standards  (FHIR/DICOM/OMOP/etc in keywords)
  I2  0-1   open license  (permissive or copyleft SPDX identifier)
  R1  0-1   citable  (mach:swhid present OR CITATION.cff in repo)
  R2  0-1   governance  (CONTRIBUTING.md in repo OR 2+ evidence items)

  Based on: FAIRsoft indicators (inab.github.io/FAIRsoft_indicators/)
            howfairis v0.15 (github.com/fair-software/howfairis)
            FAIR4RS principles (ReSA/RDA/FORCE11, 2022)

Usage:
    python scripts/suggest_judgement.py
    python scripts/suggest_judgement.py --show-all       # include matching entries
    python scripts/suggest_judgement.py --show-scores    # print score breakdown
    python scripts/suggest_judgement.py --fair-only      # show FAIR breakdown for all entries
    python scripts/suggest_judgement.py --no-fetch       # skip all API calls (offline)
    python scripts/suggest_judgement.py --refresh-cache  # delete cache and re-fetch

Set GITHUB_TOKEN env var to raise GitHub rate limit from 60 to 5000 req/hr.
Note: FAIR scoring makes 2 extra GitHub API calls per entry (CITATION.cff + CONTRIBUTING.md).
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


# ── GitHub FAIR signals (CITATION.cff + CONTRIBUTING.md existence) ───────────

def fetch_github_fair(repo_url: str) -> dict:
    """Check for CITATION.cff and CONTRIBUTING.md via GitHub Contents API.
    Returns {"has_cff": bool, "has_contributing": bool}. Cached."""
    global _gh_rate_limited
    empty = {"has_cff": False, "has_contributing": False}
    if not repo_url or "github.com" not in repo_url:
        return empty

    key = f"gh_fair:{repo_url}"
    if key in _cache:
        return _cache[key]
    if _gh_rate_limited:
        return empty

    path = repo_url.rstrip("/").replace(".git", "")
    parts = path.split("github.com/")[-1].split("/")
    if len(parts) < 2:
        return empty
    owner, repo = parts[0], parts[1]

    def _file_exists(filename: str) -> bool:
        global _gh_rate_limited
        try:
            req = urllib.request.Request(
                f"https://api.github.com/repos/{owner}/{repo}/contents/{filename}",
                headers=_gh_headers()
            )
            with urllib.request.urlopen(req, timeout=6) as resp:
                return resp.status == 200
        except urllib.error.HTTPError as e:
            if e.code in (403, 429):
                _gh_rate_limited = True
                print("  WARNING: GitHub rate limit hit -- set GITHUB_TOKEN for 5000 req/hr")
            return False
        except Exception:
            return False

    has_cff          = _file_exists("CITATION.cff")
    has_contributing = _file_exists("CONTRIBUTING.md") if not _gh_rate_limited else False

    result = {"has_cff": has_cff, "has_contributing": has_contributing}
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


# ── FAIR scoring (FAIRsoft / howfairis, max 8 pts) ───────────────────────────

HEALTH_STANDARDS = {
    "fhir", "hl7", "dicom", "openehr", "omop", "snomed", "loinc",
    "ihe", "cda", "hl7-fhir", "hl7-v2", "hl7-v3", "icd",
}

KNOWN_REPO_HOSTS = {
    "github.com", "gitlab.com", "bitbucket.org", "codeberg.org", "sr.ht",
}


def fair_score(e: dict, pypi_downloads: int = 0, do_fetch: bool = True) -> tuple[int, dict]:
    """Return (total 0-8, breakdown dict) for FAIR assessment.

    Axes (2 pts each):
      F  Findable     F1=unique-identity  F2=community-registry
      A  Accessible   A1=open-repo        A2=versioned
      I  Interoperable I1=health-standards I2=open-license
      R  Reusable     R1=citable          R2=governance
    """
    fs = {}
    repo_url = e.get("codeRepository", "") or e.get("url", "")

    # Fetch FAIR-specific GitHub signals once (shared cache)
    gh_fair = fetch_github_fair(repo_url) if do_fetch else {"has_cff": False, "has_contributing": False}

    # F1 — unique identity: both identifier and @id present
    fs["F1"] = 1 if (e.get("identifier") and e.get("@id")) else 0

    # F2 — community registry: found on PyPI (non-Python tools score 0, not penalised)
    fs["F2"] = 1 if pypi_downloads > 0 else 0

    # A1 — accessible repo on a known version-control host
    try:
        from urllib.parse import urlparse
        host = urlparse(repo_url).netloc.lower().removeprefix("www.")
        fs["A1"] = 1 if host in KNOWN_REPO_HOSTS else 0
    except Exception:
        fs["A1"] = 0

    # A2 — versioned: softwareVersion or dateModified present
    fs["A2"] = 1 if (e.get("softwareVersion") or e.get("dateModified")) else 0

    # I1 — open health standards in keywords or description
    keywords = [k.lower() for k in e.get("keywords", [])]
    desc     = e.get("description", "").lower()
    name     = e.get("name", "").lower()
    fs["I1"] = 1 if any(s in keywords or s in desc or s in name for s in HEALTH_STANDARDS) else 0

    # I2 — open license (permissive or copyleft SPDX)
    lic = e.get("license", "")
    fs["I2"] = 1 if lic in PERMISSIVE_LICENSES | COPYLEFT_LICENSES else 0

    # R1 — citable: mach:swhid present OR CITATION.cff in repo
    fs["R1"] = 1 if (e.get("mach:swhid") or gh_fair["has_cff"]) else 0

    # R2 — governance: CONTRIBUTING.md in repo OR 2+ evidence items
    evidence = e.get("mach:evidence", [])
    if isinstance(evidence, dict):
        evidence = [evidence]
    fs["R2"] = 1 if (len(evidence) >= 2 or gh_fair["has_contributing"]) else 0

    total = sum(fs.values())
    return total, fs


def fair_axes(fs: dict) -> str:
    """Format FAIR breakdown as 'F:N A:N I:N R:N'."""
    f = fs.get("F1", 0) + fs.get("F2", 0)
    a = fs.get("A1", 0) + fs.get("A2", 0)
    i = fs.get("I1", 0) + fs.get("I2", 0)
    r = fs.get("R1", 0) + fs.get("R2", 0)
    return f"F:{f} A:{a} I:{i} R:{r}"


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
    parser.add_argument("--fair-only",     action="store_true", help="Show FAIR breakdown table for all entries")
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

    # ── FAIR-only mode ────────────────────────────────────────────────────────
    if args.fair_only:
        fair_header = (
            f"{'Entry':<{LABEL_WIDTH}} "
            f"{'FAIR':>5}  "
            f"{'F1':>2} {'F2':>2}  "
            f"{'A1':>2} {'A2':>2}  "
            f"{'I1':>2} {'I2':>2}  "
            f"{'R1':>2} {'R2':>2}  "
            f"Axes"
        )
        print(fair_header)
        print("-" * (len(fair_header) + 5))
        total_fair = 0
        for e in entries:
            name    = e.get("name", e.get("identifier", "?"))[:LABEL_WIDTH - 1]
            pypi_dl = fetch_pypi_downloads(e) if do_fetch else 0
            ft, fs  = fair_score(e, pypi_downloads=pypi_dl, do_fetch=do_fetch)
            total_fair += ft
            axes = fair_axes(fs)
            fair_colour = "\033[32m" if ft >= 6 else ("\033[33m" if ft >= 4 else "\033[31m")
            print(
                f"{name:<{LABEL_WIDTH}} "
                f"{fair_colour}{ft}/8\033[0m  "
                f"{fs['F1']:>2} {fs['F2']:>2}  "
                f"{fs['A1']:>2} {fs['A2']:>2}  "
                f"{fs['I1']:>2} {fs['I2']:>2}  "
                f"{fs['R1']:>2} {fs['R2']:>2}  "
                f"{axes}"
            )
        print()
        avg = total_fair / len(entries) if entries else 0
        print(f"FAIR criteria: F1=identity F2=registry A1=repo A2=versioned I1=health-std I2=license R1=citable R2=governance")
        print(f"FAIR >= 6 = good  |  4-5 = partial  |  < 4 = limited")
        print(f"Entries: {len(entries)}  |  Average FAIR: {avg:.1f}/8")
        return

    # ── Editorial judgement table ─────────────────────────────────────────────
    mismatches = 0
    no_judgement = 0

    header = (
        f"{'Entry':<{LABEL_WIDTH}} "
        f"{'Current':<{JUDGEMENT_WIDTH}} "
        f"{'Suggested':<{JUDGEMENT_WIDTH}} "
        f"{'Pts':>4}  {'FAIR':>5}  Signals"
    )
    print(header)
    print("-" * (len(header) + 20))

    for e in entries:
        name       = e.get("name", e.get("identifier", "?"))[:LABEL_WIDTH - 1]
        current    = e.get("mach:judgement", "-")
        suggestion, bd = score_entry(e, do_fetch=do_fetch)
        total      = bd["total"]

        # FAIR score — reuse pypi_raw already fetched by score_entry
        pypi_dl = bd.get("pypi_raw", 0)
        ft, fs  = fair_score(e, pypi_downloads=pypi_dl, do_fetch=do_fetch)

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
        fair_str = f"{ft}/8"
        print(
            f"{name:<{LABEL_WIDTH}} "
            f"{colour(current, current):<{JUDGEMENT_WIDTH + 9}} "
            f"{colour(suggestion, suggestion):<{JUDGEMENT_WIDTH + 9}} "
            f"{total:>4}  {fair_str:>5}  {signals}{flag}"
        )
        if args.show_scores:
            print(f"  {'':>{LABEL_WIDTH}} editorial: {bd}")
            print(f"  {'':>{LABEL_WIDTH}} fair:       {fs}  ({fair_axes(fs)})")

    print()
    print(
        f"Signals: maturity(3) governance(3) forks(2) pypi(2) stars(1) "
        f"evidence_quality(2) license(2) evidence_count(1) = 16 max"
    )
    print(f"Thresholds: Adopt >= {ADOPT_THRESHOLD}  |  Assess >= {ASSESS_THRESHOLD}  |  Caution < {ASSESS_THRESHOLD}")
    print(f"FAIR 0-8: F1=identity F2=registry A1=repo A2=versioned I1=health-std I2=license R1=citable R2=governance")
    print(f"Entries: {len(entries)} total  |  {mismatches} mismatches  |  {no_judgement} without judgement")
    if mismatches == 0 and not args.show_all:
        print("All current judgements match suggestions.")


if __name__ == "__main__":
    main()
