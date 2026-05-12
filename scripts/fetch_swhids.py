#!/usr/bin/env python3
"""
fetch_swhids.py — compute and add mach:swhid (origin SWHID) to all MACH entries.

Origin SWHIDs are STABLE: they are derived solely from the repository URL
using a deterministic hash formula (no API call needed to compute them).
They do NOT change when new commits are pushed to the repository.

Usage:
    python scripts/fetch_swhids.py              # compute & write to all entries
    python scripts/fetch_swhids.py --dry-run    # preview only, no writes
    python scripts/fetch_swhids.py --verify     # also check SWH has crawled each repo
"""
import argparse
import hashlib
import json
import time
import urllib.error
import urllib.request
from pathlib import Path

ENTRIES_DIR = Path(__file__).parent.parent / "entries"
SWH_API = "https://archive.softwareheritage.org/api/1"
REPO_HOSTS = {"github.com", "gitlab.com", "bitbucket.org", "codeberg.org", "sr.ht"}


def origin_swhid(url: str) -> str:
    """
    Compute the stable origin SWHID from a repository URL.

    Formula (https://docs.softwareheritage.org/devel/swh-model/identifiers.html):
        sha1( utf8_bytes(url) )
    Origins use a plain SHA-1 of the URL bytes — no git-style object header.
    """
    digest = hashlib.sha1(url.encode("utf-8")).hexdigest()
    return f"swh:1:ori:{digest}"


def is_repo_url(url: str) -> bool:
    try:
        from urllib.parse import urlparse
        host = urlparse(url).netloc.lower().removeprefix("www.")
        return host in REPO_HOSTS
    except Exception:
        return False


def check_archived(repo_url: str) -> tuple[bool, str]:
    """
    Check whether Software Heritage has archived this origin.
    Returns (archived: bool, message: str).
    Rate limit: 1200 req/hr unauthenticated. We sleep 0.5s between calls.
    """
    api_url = f"{SWH_API}/origin/{repo_url}/get/"
    try:
        req = urllib.request.Request(api_url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            if resp.status == 200:
                return True, "archived"
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return False, "not yet archived in SWH — visit https://archive.softwareheritage.org/save/ to request crawl"
        return False, f"HTTP {e.code}"
    except Exception as ex:
        return False, f"error: {ex}"
    return False, "unknown"


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dry-run", action="store_true",
                        help="Print what would change without writing files")
    parser.add_argument("--verify", action="store_true",
                        help="Hit the SWH API to confirm each repo has been crawled")
    args = parser.parse_args()

    entry_files = sorted(ENTRIES_DIR.rglob("*.jsonld"))
    entry_files = [f for f in entry_files if "_template" not in f.name]

    updated = skipped = already_set = 0

    for path in entry_files:
        with open(path, encoding="utf-8") as f:
            entry = json.load(f)

        # Prefer codeRepository for repo URL, fall back to url
        repo_url = entry.get("codeRepository", "") or entry.get("url", "")
        if not repo_url or not is_repo_url(repo_url):
            print(f"  skip (no repo URL)  {path.name}")
            skipped += 1
            continue

        swhid = origin_swhid(repo_url)

        if args.verify:
            archived, msg = check_archived(repo_url)
            time.sleep(0.5)
            if not archived:
                print(f"  NOT ARCHIVED  {path.name}  — {msg}")
                skipped += 1
                continue

        existing = entry.get("mach:swhid")
        if existing == swhid:
            print(f"  unchanged    {path.name}  ->  {swhid}")
            already_set += 1
            continue

        action = "(dry-run) " if args.dry_run else ""
        print(f"  {action}set  {path.name}  ->  {swhid}")

        if not args.dry_run:
            entry["mach:swhid"] = swhid
            # Preserve original key order, append mach:swhid near the end
            with open(path, "w", encoding="utf-8") as f:
                json.dump(entry, f, indent=2, ensure_ascii=False)
                f.write("\n")
            updated += 1

    print(f"\nDone: {updated} updated, {already_set} already correct, {skipped} skipped.")
    if args.dry_run:
        print("(dry-run — no files written)")


if __name__ == "__main__":
    main()
