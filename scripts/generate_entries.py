#!/usr/bin/env python3
"""
generate_entries.py
Reads all *.jsonld files from entries/ and rewrites the entries section
of index.html with live data. Run locally or via GitHub Actions.
"""

import json
import os
import re
from pathlib import Path

ENTRIES_DIR = Path("entries")
INDEX_HTML  = Path("index.html")

CATEGORY_LABELS = {
    "clinical-systems":            "Clinical Systems",
    "interoperability-standards":  "Interoperability Standards",
    "terminologies-ontologies":    "Terminologies & Ontologies",
    "data-models-research":        "Data Models & Research Platforms",
    "medical-imaging-signals":     "Medical Imaging & Signals",
    "ai-ml-models":                "AI / ML Models",
    "datasets-benchmarks":         "Datasets & Benchmarks",
    "deidentification-privacy":    "De-identification & Privacy",
    "quality-conformance":         "Quality & Conformance",
    "public-health-epi":           "Public Health & Epi",
    "mcp-servers-ai-interfaces":   "MCP Servers & AI Interfaces",
    "tooling-infrastructure":      "Tooling & Infrastructure",
    "patient-facing-mhealth":      "Patient-Facing & mHealth",
    "compliance-governance":       "Compliance & Governance",
}

JUDGEMENT_BADGE = {
    "Adopt":       ("badge-adopt",       "Adopt"),
    "Situational": ("badge-situational", "Situational"),
    "Assess":      ("badge-assess",      "Assess"),
    "Caution":     ("badge-caution",     "Caution"),
}

def load_entries():
    entries = []
    for path in sorted(ENTRIES_DIR.rglob("*.jsonld")):
        if path.name.startswith("_"):
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            entries.append(data)
        except json.JSONDecodeError as e:
            print(f"WARN: skipping {path} — {e}")
    return entries

def category_label(cat):
    return CATEGORY_LABELS.get(cat, cat)

TYPE_LABELS = {
    "mach:MLModel":    "ML Model",
    "mach:MCPServer":  "MCP Server",
    "mach:Standard":   "Standard",
    "mach:Dataset":    "Dataset",
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

def build_url_links(e):
    site = e.get("url", "")
    repo = e.get("codeRepository", "")
    links = []
    if site:
        links.append(f'<a href="{site}" target="_blank" rel="noopener" class="entry-url">↗ site</a>')
    if repo and repo != site:
        links.append(f'<a href="{repo}" target="_blank" rel="noopener" class="entry-url">↗ repo</a>')
    return "".join(links)

def build_entries_html(entries):
    if not entries:
        return "<p style='color:var(--gray-300);font-size:0.875rem;'>No entries yet.</p>"

    rows = []
    for e in entries:
        name        = e.get("name", "—")
        description = e.get("description", "")
        cat         = e.get("mach:category", "")

        short_desc  = (description[:90] + "…") if len(description) > 92 else description
        cat_label   = category_label(cat)
        entry_type  = get_entry_type(e)
        license_str = get_license_short(e)
        jsonld_url  = get_jsonld_url(e)
        url_links   = build_url_links(e)

        lic_tag      = f'<span class="entry-lic">{license_str}</span>' if license_str else ""
        name_href    = jsonld_url if jsonld_url else e.get("url", e.get("codeRepository", "#"))

        rows.append(f"""    <div class="entry-row" data-cat="{cat}">
      <div>
        <p class="entry-name"><a href="{name_href}" target="_blank" rel="noopener" style="color:inherit;text-decoration:none;">{name}</a></p>
        <div class="entry-tags"><span class="entry-type">{entry_type}</span>{lic_tag}{url_links}</div>
        <p class="entry-desc">{short_desc}</p>
      </div>
      <span class="entry-cat">{cat_label}</span>
    </div>""")

    return "\n".join(rows)

def build_stats_html(entries):
    total    = len(entries)
    adopts   = sum(1 for e in entries if e.get("mach:judgement") == "Adopt")
    assessed = sum(1 for e in entries if e.get("mach:judgement") == "Assess")
    cats     = len(set(e.get("mach:category","") for e in entries if e.get("mach:category")))
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
