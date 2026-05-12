#!/usr/bin/env python3
"""
fetch_swhids.py — compute and add mach:swhid (origin SWHID) to all MACH entries.

Origin SWHIDs are STABLE: they are derived solely from the repository URL
using a deterministic hash formula. They do NOT change when new commits are pushed.

By default this script ONLY writes mach:swhid when Software Heritage has confirmed
it has archived the repo. This keeps the UI badge honest — it only appears once the
archive link actually resolves.

Usage:
    python scripts/fetch_swhids.py                   # write SWHID only if SWH has crawled repo
    python scripts/fetch_swhids.py --dry-run         # preview only, no writes
    python scripts/fetch_swhids.py --no-verify       # write without checking SWH (fast, offline)
    python scripts/fetch_swhids.py --verify-swhid    # confirm stored SWHID matches SWH exactly
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
    """Check whether Software Heritage has archived this origin."""
    api_url = f"{SWH_API}/origin/{repo_url}/get/"
    try:
        req = urllib.request.Request(api_url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            if resp.status == 200:
                return True, "archived"
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return False, "not yet archived — save at https://archive.softwareheritage.org/save/"
        return False, f"HTTP {e.code}"
    except Exception as ex:
        return False, f"error: {ex}"
    return False, "unknown"


def verify_swhid_against_api(repo_url: str, computed: str) -> tuple[bool, str]:
    """
    Confirm our computed SWHID matches what SWH stores.

    SWH embeds the origin SWHID in the metadata_authorities_url field of the
    origin get response, e.g.:
      .../raw-extrinsic-metadata/swhid/swh:1:ori:abc123.../authorities/
    We extract and compare it against our locally computed value.
    """
    api_url = f"{SWH_API}/origin/{repo_url}/get/"
    try:
        req = urllib.request.Request(api_url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())

        meta_url = data.get("metadata_authorities_url", "")
        # Extract swh:1:ori:... from the URL path
        swh_token = next(
            (part for part in meta_url.split("/") if part.startswith("swh:1:ori:")),
            None,
        )
        if not swh_token:
            return False, f"SWHID not found in API response: {meta_url}"
        if swh_token == computed:
            return True, f"MATCH  {swh_token}"
        return False, f"MISMATCH\n    computed: {computed}\n    SWH says: {swh_token}"

    except urllib.error.HTTPError as e:
        if e.code == 404:
            return False, "not archived in SWH"
        return False, f"HTTP {e.code}"
    except Exception as ex:
        return False, f"error: {ex}"


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dry-run", action="store_true",
                        help="Print what would change without writing files")
    parser.add_argument("--no-verify", action="store_true",
                        help="Write SWHID without checking SWH archive (fast, offline use)")
    parser.add_argument("--verify-swhid", action="store_true",
                        help="Confirm stored SWHID matches SWH exactly (implies archive check)")
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

        if args.verify_swhid:
            ok, msg = verify_swhid_against_api(repo_url, swhid)
            time.sleep(0.5)
            status = "OK  " if ok else "FAIL"
            print(f"  [{status}]  {path.name}  —  {msg}")
            if not ok:
                skipped += 1
                continue

        elif not args.no_verify:
            # Default: only write if SWH has crawled the repo
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
