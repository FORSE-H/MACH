#!/usr/bin/env python3
"""
generate_entries.py
Reads all *.jsonld files from entries/ and rewrites the entries section
of index.html with live data. Run locally or via GitHub Actions.
"""

import json
import os
import re
import sys
from pathlib import Path

ENTRIES_DIR = Path("entries")
INDEX_HTML  = Path("index.html")

sys.path.insert(0, str(Path(__file__).parent))
from taxonomy import category_labels, label as category_label

CATEGORY_LABELS = category_labels()

JUDGEMENT_BADGE = {
    "Adopt":       "badge-adopt",
    "Situational": "badge-situational",
    "Assess":      "badge-assess",
    "Caution":     "badge-caution",
}

import yaml as _yaml
FOLDER_TO_CAT = {c["folder"]: c["id"] for c in _yaml.safe_load(
    (Path(__file__).parent.parent / "data/taxonomy/categories.yaml").read_text()
)["categories"]}

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
    "mach:DataSource":    "Data Source",
    "mach:Benchmark":     "Benchmark",
    "mach:Dataset":       "Dataset",
    "schema:Dataset":     "Dataset",
    "schema:DataCatalog": "Catalog",
}

def get_entry_type(e):
    types = e.get("@type", [])
    if isinstance(types, str):
        types = [types]
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
        judgement   = e.get("mach:judgement", "")

        short_desc  = (description[:140] + "…") if len(description) > 143 else description
        cat_label   = _category_label(cat)
        entry_type  = get_entry_type(e)
        license_str = get_license_short(e)
        jsonld_url  = get_jsonld_url(e)
        url_links   = build_url_links(e)

        lic_tag       = f'<span class="entry-lic">{license_str}</span>' if license_str else ""
        name_href     = jsonld_url if jsonld_url else e.get("url", e.get("codeRepository", "#"))
        links_html    = f'<div class="entry-card-links">{url_links}</div>' if url_links else ""

        cards.append(f"""    <div class="entry-card" data-cat="{cat}" data-license="{license_str}">
      <div class="entry-card-meta">
        <span class="entry-cat">{cat_label}</span>
      </div>
      <p class="entry-name"><a href="{name_href}" target="_blank" rel="noopener">{name}</a></p>
      <div class="entry-tags"><span class="entry-type">{entry_type}</span>{lic_tag}</div>
      <p class="entry-desc">{short_desc}</p>
      {links_html}
    </div>""")

    return "\n".join(cards)

def build_stats_html(entries):
    total    = len(entries)
    adopts   = sum(1 for e in entries if e.get("mach:judgement") == "Adopt")
    assessed = sum(1 for e in entries if e.get("mach:judgement") == "Assess")
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

    entries = load_entries()
    print(f"Loaded {len(entries)} entries")

    html = INDEX_HTML.read_text(encoding="utf-8")
    patched = patch_html(html, entries)
    INDEX_HTML.write_text(patched, encoding="utf-8")

    print(f"Updated {INDEX_HTML} — {len(entries)} entries written")

if __name__ == "__main__":
    main()
