#!/usr/bin/env python3
"""
generate_entries.py
Reads all *.jsonld files from entries/ and rewrites the entries section
of index.html with live data. Run locally or via GitHub Actions.
"""

import html
import json
import re
import sys
from pathlib import Path


def esc_attr(value):
    """Escape a value for safe use inside a double-quoted HTML attribute."""
    return html.escape(str(value or ""), quote=True)

ENTRIES_DIR = Path("entries")
INDEX_HTML  = Path("index.html")

sys.path.insert(0, str(Path(__file__).parent))
from taxonomy import category_labels, label as category_label

CATEGORY_LABELS = category_labels()

JUDGEMENT_BADGE = {
    "Adopt":   "badge-adopt",
    "Assess":  "badge-assess",
    "Caution": "badge-caution",
}

import yaml as _yaml
FOLDER_TO_CAT = {c["folder"]: c["id"] for c in _yaml.safe_load(
    (Path(__file__).parent.parent / "data/taxonomy/categories.yaml").read_text()
)["categories"]}

SIGNALS_PATH = Path("data/signals.json")


def load_signals():
    """Load the harvested signals (stars, scorer judgement, lineage) keyed by
    identifier. Absent file → empty dict, so the site still builds without it."""
    if not SIGNALS_PATH.exists():
        print("NOTE: data/signals.json not found — rendering without harvested signals")
        return {}
    data = json.loads(SIGNALS_PATH.read_text(encoding="utf-8"))
    return {e["identifier"]: e for e in data.get("entries", [])}


def _fmt_count(n):
    """9018 -> '9,018'; large numbers -> '9.0k'."""
    if n is None:
        return None
    if n >= 10000:
        return f"{n/1000:.0f}k"
    if n >= 1000:
        return f"{n/1000:.1f}k"
    return f"{n:,}"


SIGNALS = {}  # populated in main()

def load_entries():
    entries = []
    for path in sorted(ENTRIES_DIR.rglob("*.jsonld")):
        if path.name.startswith("_"):
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            folder = path.parent.name
            data["_cat"] = FOLDER_TO_CAT.get(folder, folder)
            entries.append(data)
        except json.JSONDecodeError as e:
            print(f"WARN: skipping {path} — {e}")
    return entries

def _category_label(cat):
    return category_label(cat)

TYPE_LABELS = {
    "mach:MLModel":       "ML Model",
    "mach:MCPServer":     "MCP Server",
    "mach:Standard":      "Standard",
    "mach:Spec":          "Standard",
    "mach:DataSource":    "Data Source",
    "mach:Benchmark":     "Benchmark",
    "mach:Dataset":       "Dataset",
    "schema:Dataset":     "Dataset",
    "schema:DataCatalog": "Catalog",
}

# mach:subcategory → display label for the type pill. The subcategory is the
# authoritative, consistently-set field; @type is not (some MCP servers lack
# mach:MCPServer in @type), so when a subcategory maps here we use it.
SUBCATEGORY_TYPE_LABELS = {
    "mcp-server":    "MCP Server",
    "ai-agent":      "AI Agent",
    "agent-skills":  "Agent Skills",
    "ai-swarm":      "Agent Swarm",
}

# mach:category → type-pill label, used as a reliable fallback when @type is
# missing or inconsistent. The folder-derived category is always correct, so a
# model mislabelled in @type still shows "ML Model", a data-source shows "Data
# Source", etc. Benchmarks keep their own label via @type (checked first).
CATEGORY_TYPE_LABELS = {
    "ai-ml-models":  "ML Model",
    "data-sources":  "Data Source",
    "datasets":      "Dataset",
    "specs":         "Standard",
    "catalogs":      "Catalog",
    "software":      "Software",
    "hardware":      "Hardware",
}

def get_entry_type(e):
    # 1. Subcategory wins when it names a concrete tool type (ai-tooling).
    sub = e.get("mach:subcategory", "")
    if sub in SUBCATEGORY_TYPE_LABELS:
        return SUBCATEGORY_TYPE_LABELS[sub]

    types = e.get("@type", [])
    if isinstance(types, str):
        types = [types]

    # 2. A distinctive @type (Benchmark) that the category can't express.
    if "mach:Benchmark" in types:
        return "Benchmark"

    # 3. The folder-derived category — always correct, unlike @type ordering.
    cat = e.get("_cat", "")
    if cat in CATEGORY_TYPE_LABELS:
        return CATEGORY_TYPE_LABELS[cat]

    # 4. Fall back to @type, then Software.
    for key, label in TYPE_LABELS.items():
        if key in types:
            return label
    return "Software"

def get_license_short(e):
    lic = e.get("license", "")
    if not lic:
        return ""
    if lic.startswith("http"):
        return lic.rstrip("/").split("/")[-1]
    return lic

# Collapse the long tail of raw licence strings into a handful of buckets people
# actually navigate by. The raw licence still shows on the card and detail page;
# this is only for the filter. Order matters: non-commercial is checked before
# the generic CC/open-data bucket so a CC-BY-NC lands in "non-commercial".
def license_bucket(e):
    lic = (get_license_short(e) or "").upper()
    if not lic:
        return "none"
    if "NO-LICENSE" in lic or "NOASSERTION" in lic or lic in ("NONE", "OTHER"):
        return "none"
    # Non-commercial first (a CC-BY-NC must not fall into open-data).
    if "-NC-" in lic or lic.endswith("-NC") or "NON-COMMERCIAL" in lic or "NONCOMMERCIAL" in lic:
        return "noncommercial"
    permissive = ("MIT", "APACHE", "BSD", "ISC", "0BSD", "ZLIB", "UNLICENSE", "W3C", "NEMA")
    if any(p in lic for p in permissive):
        return "permissive"
    copyleft = ("GPL", "AGPL", "LGPL", "MPL", "EUPL", "EPL", "CDDL")
    if any(p in lic for p in copyleft):
        return "copyleft"
    opendata = ("CC-BY", "CC0", "CC-0", "OGL", "PUBLIC-DOMAIN", "PUBLIC DOMAIN",
                "GOVERNMENT-PUBLIC-DOMAIN", "FREELY-REUSABLE", "FREE-TO-USE",
                "ISO-COPYRIGHT", "NCBO", "CHDL")
    if any(p in lic for p in opendata):
        return "opendata"
    return "custom"


def get_jsonld_url(e):
    entry_id = e.get("@id", "")
    if "tree/main" in entry_id:
        return entry_id.replace("tree/main", "blob/main") + ".jsonld"
    return ""

REPO_HOSTS = {"github.com", "gitlab.com", "bitbucket.org", "codeberg.org", "sr.ht"}

def _is_repo_url(url):
    try:
        from urllib.parse import urlparse
        host = urlparse(url).netloc.lower().removeprefix("www.")
        return host in REPO_HOSTS
    except Exception:
        return False

def build_url_links(e):
    site   = e.get("url", "")
    repo   = e.get("codeRepository", "")
    swhid  = e.get("mach:swhid", "")
    hf_url = e.get("mach:huggingFaceUrl", "")
    links = []
    if site:
        label = "repo" if _is_repo_url(site) else "site"
        links.append(f'<a href="{site}" target="_blank" rel="noopener" class="entry-url">&#8599; {label}</a>')
    if repo and repo != site:
        links.append(f'<a href="{repo}" target="_blank" rel="noopener" class="entry-url">&#8599; repo</a>')
    if swhid:
        swh_url = f"https://archive.softwareheritage.org/browse/origin/?origin_url={repo or site}"
        links.append(f'<a href="{swh_url}" target="_blank" rel="noopener" class="entry-url entry-swh" title="Archived on Software Heritage&#10;{swhid}"><img src="logos/swh.svg" alt="" class="swh-icon">swh</a>')
    if hf_url:
        links.append(f'<a href="{hf_url}" target="_blank" rel="noopener" class="entry-url entry-hf" title="Available on HuggingFace Hub"><img src="logos/hf.svg" alt="" class="hf-icon">hf</a>')
    return "".join(links)

def build_entries_html(entries):
    if not entries:
        return "<p style='color:var(--gray-300);font-size:0.875rem;'>No entries yet.</p>"

    cards = []
    for e in entries:
        name        = e.get("name", "—")
        description = e.get("description", "")
        cat         = e.get("_cat", "")

        short_desc  = (description[:140] + "…") if len(description) > 143 else description
        cat_label   = _category_label(cat)
        entry_type  = get_entry_type(e)
        license_str = get_license_short(e)
        jsonld_url  = get_jsonld_url(e)
        url_links   = build_url_links(e)

        license_url   = e.get("mach:licenseUrl")
        if license_str and license_url:
            lic_tag = f'<a href="{license_url}" target="_blank" rel="noopener" class="entry-lic" title="Licence">{license_str}</a>'
        elif license_str:
            lic_tag = f'<span class="entry-lic">{license_str}</span>'
        else:
            lic_tag = ""

        # ── Rule-based judgement from the harvested scorer (not hand-written) ──
        ident = e.get("identifier", "")
        sig   = SIGNALS.get(ident, {})
        scorer_judgement = sig.get("judgement")          # Adopt/Assess/Caution or None
        scorer_reason    = sig.get("judgement_reason") or ""
        signals          = sig.get("signals", {}) or {}

        if scorer_judgement in ("Adopt", "Assess", "Caution"):
            judgement = scorer_judgement
            j_title   = scorer_reason.replace('"', "&quot;")
            judgement_badge = (
                f'<span class="entry-judgement ring-{judgement.lower()}" '
                f'title="{j_title}">{judgement}</span>'
            )
        else:
            # No harvestable signal → not auto-scored (datasets, specs, hosted services).
            judgement = ""
            judgement_badge = (
                '<span class="entry-judgement ring-none" '
                'title="No harvestable repository signal — not auto-scored">not scored</span>'
            )

        # ── Stars badge (from harvested GitHub signals) ──
        stars = _fmt_count(signals.get("repo_stars"))
        stars_badge = (
            f'<span class="entry-stars" title="GitHub stars">&#9733; {stars}</span>'
            if stars else ""
        )

        # ── Primary language chip + repo-health dot ──
        lang = signals.get("primary_language")
        lang_chip = f'<span class="entry-lang">{lang}</span>' if lang else ""
        health = signals.get("repo_health")
        health_dot = (
            f'<span class="entry-health health-{health.lower()}" title="Repo health: {health}'
            f'{" — " + signals.get("repo_health_reason") if signals.get("repo_health_reason") else ""}">&#9679;</span>'
            if health else ""
        )

        # ── Per-entry links: detail page, repo/site, raw JSON-LD ──
        detail_href = f"entry/{ident}.html"
        jsonld_link = (
            f'<a href="{jsonld_url}" target="_blank" rel="noopener" class="entry-url entry-jsonld" '
            f'title="View raw JSON-LD metadata">&#123;&#125; JSON-LD</a>'
            if jsonld_url else ""
        )
        detail_link = f'<a href="{detail_href}" class="entry-url entry-detail" title="Signals &amp; lineage">&#8505; details</a>'
        links_html  = f'<div class="entry-card-links">{detail_link}{url_links}{jsonld_link}</div>'

        # ── Faceting attributes (from harvested signals + entry metadata) ──
        lic_bucket = license_bucket(e)
        lang_val   = (signals.get("primary_language") or "").strip()
        health_val = (signals.get("repo_health") or "").strip().lower()
        gov_val    = (e.get("mach:governance") or "").strip().lower()
        on_pypi    = "1" if signals.get("pypi_downloads") not in (None, "", 0) else ""
        on_hf      = "1" if signals.get("hf_downloads") not in (None, "", 0) \
                             or e.get("mach:huggingFaceUrl") else ""

        cards.append(f"""    <div class="entry-card" data-cat="{cat}" data-license="{license_str}" data-license-bucket="{lic_bucket}" data-lang="{esc_attr(lang_val)}" data-health="{health_val}" data-governance="{gov_val}" data-pypi="{on_pypi}" data-hf="{on_hf}" data-judgement="{judgement}">
      <div class="entry-card-meta">
        <span class="entry-cat">{cat_label}</span>{stars_badge}{judgement_badge}
      </div>
      <p class="entry-name"><a href="{detail_href}" class="entry-name-link" title="Open details &amp; lineage">{name}</a></p>
      <div class="entry-tags"><span class="entry-type">{entry_type}</span>{lic_tag}{lang_chip}{health_dot}</div>
      <p class="entry-desc">{short_desc}</p>
      {links_html}
    </div>""")

    return "\n".join(cards)

def _entry_judgement(e):
    """The rule-based (scorer) judgement for an entry, or '' if not auto-scored."""
    j = SIGNALS.get(e.get("identifier", ""), {}).get("judgement")
    return j if j in ("Adopt", "Assess", "Caution") else ""

def build_stats_html(entries):
    total    = len(entries)
    adopts   = sum(1 for e in entries if _entry_judgement(e) == "Adopt")
    assessed = sum(1 for e in entries if _entry_judgement(e) == "Assess")
    cats     = len(set(e.get("_cat","") for e in entries if e.get("_cat")))
    return total, adopts, assessed, cats

def patch_html(html, entries):
    entry_html = build_entries_html(entries)
    total, adopts, assessed, cats = build_stats_html(entries)

    # ── Replace the entries list block ──────────────────────────────────────
    html = re.sub(
        r'<!-- ENTRIES:START -->.*?<!-- ENTRIES:END -->',
        f'<!-- ENTRIES:START -->\n{entry_html}\n    <!-- ENTRIES:END -->',
        html,
        flags=re.DOTALL
    )

    # ── Replace stat numbers ─────────────────────────────────────────────────
    html = re.sub(
        r'<!-- STAT:TOTAL -->[^<]*<!-- /STAT:TOTAL -->',
        f'<!-- STAT:TOTAL -->{total}<!-- /STAT:TOTAL -->',
        html
    )
    html = re.sub(
        r'<!-- STAT:ADOPT -->[^<]*<!-- /STAT:ADOPT -->',
        f'<!-- STAT:ADOPT -->{adopts}<!-- /STAT:ADOPT -->',
        html
    )
    html = re.sub(
        r'<!-- STAT:ASSESS -->[^<]*<!-- /STAT:ASSESS -->',
        f'<!-- STAT:ASSESS -->{assessed}<!-- /STAT:ASSESS -->',
        html
    )
    html = re.sub(
        r'<!-- STAT:CATS -->[^<]*<!-- /STAT:CATS -->',
        f'<!-- STAT:CATS -->{cats}<!-- /STAT:CATS -->',
        html
    )

    return html

def main():
    if not INDEX_HTML.exists():
        print(f"ERROR: {INDEX_HTML} not found")
        raise SystemExit(1)

    global SIGNALS
    SIGNALS = load_signals()

    entries = load_entries()
    scored = sum(1 for e in entries if _entry_judgement(e))
    print(f"Loaded {len(entries)} entries ({scored} auto-scored, "
          f"{len(entries) - scored} not scored); {len(SIGNALS)} signal records")

    html = INDEX_HTML.read_text(encoding="utf-8")
    patched = patch_html(html, entries)
    INDEX_HTML.write_text(patched, encoding="utf-8")

    print(f"Updated {INDEX_HTML} — {len(entries)} entries written")

    # Keep README's entry/category counts in lockstep with index.html, so the
    # consistency gate (scripts/check_consistency.py) never flags drift after a
    # normal regeneration. Best-effort: never fail generation if it's missing.
    try:
        import subprocess
        subprocess.run(
            [sys.executable, "scripts/check_consistency.py", "--write"],
            check=False,
        )
    except Exception as exc:  # pragma: no cover
        print(f"(consistency sync skipped: {exc})")

if __name__ == "__main__":
    main()
