#!/usr/bin/env python3
"""
Check all URLs in MACH JSON-LD entries for broken links.

Usage:
  python3 scripts/check_urls.py                          # check all entries
  python3 scripts/check_urls.py --output report.md       # write markdown report
  python3 scripts/check_urls.py --primary-only FILE ...  # check specific files, primary URLs only

Exit codes:
  0  all primary URLs OK (warnings may exist for secondary URLs)
  1  one or more primary URLs returned 404
"""
import argparse
import concurrent.futures
import json
import glob
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import date

# Domains that routinely block bots or are paywalled.
# 404s from these are still reported. 403/401 are treated as warnings only.
PAYWALL_OR_BOTBLOCK = {
    "clinicaltrials.gov",
    "gatk.broadinstitute.org",
    "pubs.rsna.org",
    "www.unispital-basel.ch",
    "www.vitasystems.de",
    "vitasystems.de",
    "www.nature.com",
    "nature.com",
    "ai.nejm.org",
    "www.nejm.org",
    "www.cms.gov",
    "cms.gov",
    "www.kaggle.com",
    "kaggle.com",
    "join.slack.com",
    "discord.gg",
    "academic.oup.com",
    "www.healthaffairs.org",
    "healthaffairs.org",
    "link.springer.com",
    "springer.com",
    "www.sciencedirect.com",
    "sciencedirect.com",
}

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (MACH-link-checker/1.0; "
        "+https://github.com/FORSE-H/MACH)"
    )
}


def domain(url: str) -> str:
    return urllib.parse.urlparse(url).netloc


def collect_urls(entry_files):
    """Return {url: {"files": [...], "primary": bool}}."""
    url_map: dict = {}

    def record(url, filepath, primary):
        if not url.startswith("http"):
            return
        info = url_map.setdefault(url, {"files": [], "primary": False})
        if filepath not in info["files"]:
            info["files"].append(filepath)
        if primary:
            info["primary"] = True

    def walk(obj, filepath):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k in ("url", "codeRepository") and isinstance(v, str):
                    record(v, filepath, primary=True)
                elif k == "relatedLink":
                    targets = [v] if isinstance(v, str) else (v if isinstance(v, list) else [])
                    for u in targets:
                        if isinstance(u, str):
                            record(u, filepath, primary=False)
                elif k == "mach:evidence" and isinstance(v, list):
                    for item in v:
                        if isinstance(item, dict):
                            u = item.get("url", "")
                            if u:
                                record(u, filepath, primary=False)
                else:
                    walk(v, filepath)
        elif isinstance(obj, list):
            for item in obj:
                walk(item, filepath)

    for filepath in entry_files:
        try:
            with open(filepath, encoding="utf-8") as f:
                walk(json.load(f), filepath)
        except Exception:
            pass

    return url_map


def check(url: str):
    """Return (url, status_code_or_None, error_string_or_None)."""
    try:
        req = urllib.request.Request(url, method="HEAD", headers=HEADERS)
        resp = urllib.request.urlopen(req, timeout=15, context=CTX)
        return url, resp.status, None
    except urllib.error.HTTPError as e:
        if e.code == 405:
            # HEAD not allowed — retry with GET
            try:
                req2 = urllib.request.Request(url, headers=HEADERS)
                resp2 = urllib.request.urlopen(req2, timeout=15, context=CTX)
                return url, resp2.status, None
            except urllib.error.HTTPError as e2:
                return url, e2.code, None
            except Exception as e2:
                return url, None, str(e2)[:120]
        return url, e.code, None
    except Exception as e:
        return url, None, str(e)[:120]


def classify(url, status, err, is_primary):
    """Return 'ok', 'broken', or 'warn'."""
    if err:
        return "warn"  # network/timeout — may be transient
    if status and status < 400:
        return "ok"
    if status == 404:
        return "broken"  # 404 is always broken regardless of domain
    # 403/401/other non-200 on known paywall/bot-block domains → warn only
    if domain(url) in PAYWALL_OR_BOTBLOCK:
        return "warn"
    if status in (401, 403):
        return "warn"
    return "warn"  # 5xx etc — don't hard-fail on server errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="*", help="Specific entry files (default: all)")
    parser.add_argument("--primary-only", action="store_true", help="Only check primary URLs")
    parser.add_argument("--output", metavar="FILE", help="Write markdown report to FILE")
    args = parser.parse_args()

    if args.files:
        entries = args.files
    else:
        entries = glob.glob("entries/**/*.jsonld", recursive=True)
        entries = [e for e in entries if "_template" not in e]

    url_map = collect_urls(entries)

    if args.primary_only:
        url_map = {u: v for u, v in url_map.items() if v["primary"]}

    print(f"Checking {len(url_map)} URLs across {len(entries)} entries...", flush=True)

    results: dict = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as pool:
        future_to_url = {pool.submit(check, u): u for u in url_map}
        for i, fut in enumerate(concurrent.futures.as_completed(future_to_url), 1):
            url, status, err = fut.result()
            info = url_map[url]
            verdict = classify(url, status, err, info["primary"])
            results[url] = {
                "status": status,
                "err": err,
                "verdict": verdict,
                "primary": info["primary"],
                "files": info["files"],
            }
            if i % 50 == 0:
                print(f"  {i}/{len(url_map)} checked...", flush=True)

    broken = {u: v for u, v in results.items() if v["verdict"] == "broken"}
    warnings = {u: v for u, v in results.items() if v["verdict"] == "warn"}
    ok_count = sum(1 for v in results.values() if v["verdict"] == "ok")

    # Console summary
    print(f"\nResults: {ok_count} OK | {len(warnings)} warnings | {len(broken)} broken")

    if broken:
        print("\nBROKEN (404):")
        for url, info in sorted(broken.items()):
            primary_flag = "[primary]" if info["primary"] else "[secondary]"
            files = ", ".join(info["files"])
            print(f"  404 {primary_flag} {url}")
            print(f"      in: {files}")

    if warnings:
        print("\nWARNINGS (403/401/timeout — verify manually):")
        for url, info in sorted(warnings.items()):
            label = info["status"] if info["status"] else f"ERR:{info['err']}"
            files = ", ".join(info["files"])
            print(f"  {label} {url}")
            print(f"      in: {files}")

    # Markdown report
    if args.output:
        lines = [
            f"## MACH URL check — {date.today()}",
            "",
            f"**{len(url_map)} URLs checked** across {len(entries)} entries: "
            f"{ok_count} OK · {len(warnings)} warnings · **{len(broken)} broken**",
            "",
        ]

        if broken:
            lines += [
                "### Broken URLs (404 — need fixing)",
                "",
                "| URL | Type | Entry file |",
                "|-----|------|------------|",
            ]
            for url, info in sorted(broken.items()):
                kind = "primary" if info["primary"] else "secondary"
                files = "<br>".join(info["files"])
                lines.append(f"| {url} | {kind} | {files} |")
            lines.append("")
        else:
            lines += ["### Broken URLs", "", "_None found._", ""]

        if warnings:
            lines += [
                "### Warnings (paywall / bot-block / transient — verify manually)",
                "",
                "| URL | Status | Entry file |",
                "|-----|--------|------------|",
            ]
            for url, info in sorted(warnings.items()):
                label = str(info["status"]) if info["status"] else f"ERR"
                files = "<br>".join(info["files"])
                lines.append(f"| {url} | {label} | {files} |")
            lines.append("")

        with open(args.output, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        print(f"\nReport written to {args.output}")

    return 1 if broken else 0


if __name__ == "__main__":
    sys.exit(main())
