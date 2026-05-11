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
    "interoperability-standards":  "Interop Standards",
    "terminologies-ontologies":    "Terminologies",
    "data-models-research":        "Data Models",
    "medical-imaging-signals":     "Imaging & Signals",
    "ai-ml-models":                "AI / ML Models",
    "datasets-benchmarks":         "Datasets",
    "deidentification-privacy":    "De-id & Privacy",
    "quality-conformance":         "Quality",
    "public-health-epi":           "Public Health",
    "mcp-servers-ai-interfaces":   "MCP Servers",
    "tooling-infrastructure":      "Tooling",
    "patient-facing-mhealth":      "Patient-Facing",
    "compliance-governance":       "Compliance",
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

def build_entries_html(entries):
    if not entries:
        return "<p style='color:var(--gray-300);font-size:0.875rem;'>No entries yet.</p>"

    rows = []
    for e in entries:
        name        = e.get("name", "—")
        description = e.get("description", "")
        url         = e.get("url", e.get("codeRepository", "#"))
        cat         = e.get("mach:category", "")
        judgement   = e.get("mach:judgement", "")

        # Truncate description to ~80 chars for table display
        short_desc = (description[:78] + "…") if len(description) > 80 else description

        cat_label = category_label(cat)
        badge_cls, badge_text = JUDGEMENT_BADGE.get(judgement, ("badge-caution", judgement))

        rows.append(f"""    <div class="entry-row">
      <div>
        <p class="entry-name"><a href="{url}" target="_blank" rel="noopener" style="color:inherit;text-decoration:none;">{name}</a></p>
        <p class="entry-desc">{short_desc}</p>
      </div>
      <span class="entry-cat">{cat_label}</span>
      <span class="badge {badge_cls}">{badge_text}</span>
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
