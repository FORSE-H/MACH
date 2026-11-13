#!/usr/bin/env python3
"""generate_entry_pages.py — one static detail page per entry, under entry/.

Each page shows the rule-based judgement (with the scorer's reason), the
harvested signals, the full "Signals & lineage" table (every field → value →
source), and the change history (deviations). Data comes from data/signals.json
(baked at build time by the harvester) plus the entry's own JSON-LD for the
editorial/descriptive fields. No runtime API calls.
"""

from __future__ import annotations

import html
import json
from pathlib import Path

ENTRIES_DIR = Path("entries")
OUT_DIR = Path("entry")
SIGNALS_PATH = Path("data/signals.json")

_FIELD_LABELS = {
    "description": "description",
    "license": "license",
    "repo_stars": "GitHub stars",
    "repo_forks": "GitHub forks",
    "repo_last_commit": "last commit",
    "repo_created": "repository created",
    "repo_archived": "archived",
    "repo_open_issues": "open issues",
    "repo_primary_language": "primary language",
    "repo_languages": "languages",
    "repo_topics": "topics",
    "repo_homepage": "homepage",
    "has_tests": "has tests",
    "has_ci": "has CI",
    "has_docs": "has docs",
    "has_releases": "has releases",
    "pypi_downloads": "PyPI downloads (monthly)",
    "hf_downloads": "HuggingFace downloads (monthly)",
    "judgement": "judgement",
    "judgement_reason": "judgement reason",
    "repo_health": "repo health",
    "repo_health_reason": "repo health reason",
}


def esc(s) -> str:
    return html.escape(str(s)) if s is not None else ""


def load_signals() -> dict:
    if not SIGNALS_PATH.exists():
        return {}
    data = json.loads(SIGNALS_PATH.read_text(encoding="utf-8"))
    return {e["identifier"]: e for e in data.get("entries", [])}


def load_entries() -> dict:
    out = {}
    for p in sorted(ENTRIES_DIR.rglob("*.jsonld")):
        if p.name.startswith("_"):
            continue
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
            d["_folder"] = p.parent.name
            d["_jsonld_path"] = f"entries/{p.parent.name}/{p.name}"
            out[d["identifier"]] = d
        except (json.JSONDecodeError, KeyError):
            continue
    return out


def _jsonld_url(entry) -> str:
    aid = entry.get("@id", "")
    if "tree/main" in aid:
        return aid.replace("tree/main", "blob/main") + ".jsonld"
    return ""


RING_CLASS = {"Adopt": "ring-adopt", "Assess": "ring-assess", "Caution": "ring-caution"}


_HEALTH_CLASS = {
    "Active": "ok", "Maintained": "ok",
    "Dormant": "warn", "Stale": "warn", "Unknown": "warn",
    "Archived": "bad",
}


def _spec_name_from_url(url: str) -> str:
    """entries/specs/fhir-r4 → 'fhir-r4'. Falls back to the last path segment."""
    return url.rstrip("/").split("/")[-1]


def _repo_section(signals: dict, entry: dict) -> str:
    """Repository health, languages, and code-health checklist — the 'is this a
    serious, living codebase?' panel. Returns '' when there is nothing to show."""
    health = signals.get("repo_health")
    health_reason = signals.get("repo_health_reason") or ""
    langs = signals.get("languages")  # "Python:82,C++:15"
    stars = signals.get("repo_stars")
    forks = signals.get("repo_forks")
    issues = signals.get("repo_open_issues")
    checks = [("tests", signals.get("has_tests")), ("CI", signals.get("has_ci")),
              ("docs", signals.get("has_docs")), ("releases", signals.get("has_releases"))]

    # Standards this tool implements (curated mach:supportsSpec on the entry).
    specs = entry.get("mach:supportsSpec") or []
    if isinstance(specs, str):
        specs = [specs]

    if not any([health, langs, stars is not None, any(v is not None for _, v in checks), specs]):
        return ""

    parts = ['<section class="repo">', "<h3>Repository</h3>"]

    if health:
        cls = _HEALTH_CLASS.get(health, "warn")
        parts.append(
            f'<p class="health {cls}"><span class="dot"></span><strong>{esc(health)}</strong>'
            f'<span class="muted"> — {esc(health_reason)}</span></p>'
        )

    # Headline counts
    counts = []
    if stars is not None:  counts.append(f"&#9733; {stars:,} stars")
    if forks is not None:  counts.append(f"{forks:,} forks")
    if issues is not None: counts.append(f"{issues:,} open issues")
    if counts:
        parts.append(f'<p class="counts">{" · ".join(counts)}</p>')

    # Language breakdown bar
    if langs:
        pairs = []
        for tok in langs.split(","):
            if ":" in tok:
                lang, pct = tok.split(":", 1)
                try:
                    pairs.append((lang, int(pct)))
                except ValueError:
                    pass
        if pairs:
            bar = "".join(
                f'<span class="seg" style="width:{pct}%" title="{esc(lang)} {pct}%"></span>'
                for lang, pct in pairs
            )
            legend = " ".join(f'<span class="lg">{esc(lang)} {pct}%</span>' for lang, pct in pairs[:5])
            parts.append(f'<div class="langbar">{bar}</div><p class="legend">{legend}</p>')

    # Code-health checklist
    if any(v is not None for _, v in checks):
        items = "".join(
            f'<li class="{"yes" if v else "no"}">{"✓" if v else "✕"} {name}</li>'
            for name, v in checks if v is not None
        )
        parts.append(f'<ul class="checks">{items}</ul>')

    # Standards implemented
    if specs:
        chips = " ".join(
            f'<a class="spec-chip" href="../entry/{esc(_spec_name_from_url(s))}.html">{esc(_spec_name_from_url(s))}</a>'
            for s in specs
        )
        parts.append(f'<p class="implements"><span class="muted">Implements:</span> {chips}</p>')

    parts.append("</section>")
    return "\n    ".join(parts)


def render_page(entry: dict, sig: dict) -> str:
    ident = entry["identifier"]
    name = entry.get("name", ident)
    desc = entry.get("description", "")
    url = entry.get("url", "")
    repo = entry.get("codeRepository", "")
    jsonld_url = _jsonld_url(entry)

    judgement = (sig or {}).get("judgement")
    reason = (sig or {}).get("judgement_reason") or ""
    facts = (sig or {}).get("facts", []) or []
    history = (sig or {}).get("history", []) or []
    signals = (sig or {}).get("signals", {}) or {}

    repo_block = _repo_section(signals, entry)

    if judgement in RING_CLASS:
        badge = f'<span class="ring {RING_CLASS[judgement]}">{esc(judgement)}</span>'
        judgement_block = f"""<div class="verdict">
      <h2>Judgement: {esc(judgement)}</h2>
      <p>{esc(reason)}</p>
      <p class="muted">Derived deterministically by the MACH scorer from the signals below — not written prose.</p>
    </div>"""
    else:
        badge = '<span class="ring ring-none">not scored</span>'
        judgement_block = """<div class="verdict">
      <h2>Not auto-scored</h2>
      <p class="muted">This entry has no harvestable repository signal (e.g. a dataset, standard, or hosted service), so the deterministic scorer does not assign a ring.</p>
    </div>"""

    # Signals & lineage table
    if facts:
        rows = []
        for f in sorted(facts, key=lambda x: x["field_name"]):
            label = _FIELD_LABELS.get(f["field_name"], f["field_name"])
            val = f["value"]
            status = f.get("fetch_status", "")
            val_disp = esc(val) if val not in (None, "") else f'<span class="muted">{esc(status or "—")}</span>'
            rows.append(
                f'<tr><td class="field">{esc(label)}</td>'
                f'<td class="value">{val_disp}</td>'
                f'<td class="source"><code>{esc(f.get("source_id","—"))}</code></td></tr>'
            )
        lineage = f"""<section>
      <h3>Signals &amp; lineage</h3>
      <p class="muted">Every value records the source it was harvested from.</p>
      <table class="lineage">
        <thead><tr><th>Field</th><th>Value</th><th>Source</th></tr></thead>
        <tbody>{''.join(rows)}</tbody>
      </table>
    </section>"""
    else:
        lineage = ""

    # Change history / deviations
    if history:
        hrows = []
        for h in history:
            hrows.append(
                f'<tr><td>{esc(h.get("changed_at",""))}</td>'
                f'<td class="field">{esc(h.get("field_name",""))}</td>'
                f'<td class="muted">{esc(h.get("previous_value") or "—")}</td>'
                f'<td>{esc(h.get("value") or "—")}</td>'
                f'<td><code>{esc(h.get("source_id","—"))}</code></td></tr>'
            )
        history_block = f"""<section>
      <h3>Change history</h3>
      <p class="muted">Recorded deviations — when a harvested value changed between runs.</p>
      <table class="lineage">
        <thead><tr><th>When</th><th>Field</th><th>Was</th><th>Now</th><th>Source</th></tr></thead>
        <tbody>{''.join(hrows)}</tbody>
      </table>
    </section>"""
    else:
        history_block = """<section>
      <h3>Change history</h3>
      <p class="muted">No recorded deviations yet — values have not changed since first harvest.</p>
    </section>"""

    links = []
    if url:
        links.append(f'<a href="{esc(url)}" target="_blank" rel="noopener">&#8599; {"Repository" if "github.com" in url else "Website"}</a>')
    if repo and repo != url:
        links.append(f'<a href="{esc(repo)}" target="_blank" rel="noopener">&#8599; Repository</a>')
    if jsonld_url:
        links.append(f'<a href="{esc(jsonld_url)}" target="_blank" rel="noopener">&#123;&#125; View JSON-LD</a>')

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(name)} — MACH</title>
<style>
  :root {{
    --teal-700:#0F6E56; --teal-300:#5EC9A6; --teal-50:#E1F5EE;
    --amber-dark:#B45309; --amber-light:#FFFBEB; --rose:#BE123C; --rose-light:#FFF1F2;
    --ink:#1a2027; --muted:#6b7684; --border:#e4e8ec; --bg:#fbfcfd; --card:#fff;
  }}
  * {{ box-sizing:border-box; margin:0; padding:0; }}
  body {{ font-family:-apple-system,'Segoe UI',system-ui,sans-serif; background:var(--bg); color:var(--ink); line-height:1.55; }}
  .wrap {{ max-width:860px; margin:0 auto; padding:32px 16px 64px; }}
  a {{ color:var(--teal-700); text-decoration:none; }}
  a:hover {{ text-decoration:underline; }}
  .back {{ font-size:0.85rem; color:var(--muted); }}
  h1 {{ font-size:2rem; margin:12px 0 4px; display:flex; align-items:center; gap:12px; flex-wrap:wrap; }}
  .desc {{ color:#39434d; margin:8px 0 16px; }}
  .links {{ display:flex; gap:18px; flex-wrap:wrap; font-size:0.9rem; margin-bottom:20px; }}
  .ring {{ font-family:'DM Mono',monospace; font-size:0.7rem; font-weight:600; text-transform:uppercase; letter-spacing:0.06em; padding:3px 10px; border-radius:999px; border:1px solid; }}
  .ring-adopt {{ color:var(--teal-700); border-color:var(--teal-300); background:var(--teal-50); }}
  .ring-assess {{ color:var(--amber-dark); border-color:#FCD34D; background:var(--amber-light); }}
  .ring-caution {{ color:var(--rose); border-color:#FDA4AF; background:var(--rose-light); }}
  .ring-none {{ color:var(--muted); border-color:var(--border); background:#f3f5f7; }}
  .verdict {{ background:var(--card); border:1px solid var(--border); border-radius:10px; padding:18px 20px; margin:16px 0 28px; }}
  .verdict h2 {{ font-size:1.05rem; margin-bottom:8px; }}
  .muted {{ color:var(--muted); font-size:0.85rem; }}
  section {{ margin:28px 0; }}
  h3 {{ font-size:1rem; margin-bottom:6px; }}
  table.lineage {{ width:100%; border-collapse:collapse; margin-top:12px; font-size:0.85rem; }}
  table.lineage th {{ text-align:left; color:var(--muted); font-weight:600; font-size:0.7rem; text-transform:uppercase; letter-spacing:0.05em; padding:8px 10px; border-bottom:2px solid var(--border); }}
  table.lineage td {{ padding:9px 10px; border-bottom:1px solid var(--border); vertical-align:top; }}
  td.field {{ font-family:'DM Mono',monospace; color:#39434d; white-space:nowrap; }}
  td.value {{ word-break:break-word; }}
  td.source code, td code {{ font-family:'DM Mono',monospace; font-size:0.78rem; background:#f0f3f5; padding:2px 6px; border-radius:4px; color:#4a5560; }}
  footer {{ margin-top:48px; padding-top:20px; border-top:1px solid var(--border); font-size:0.8rem; color:var(--muted); }}
  /* Repository panel */
  section.repo {{ background:var(--card); border:1px solid var(--border); border-radius:10px; padding:16px 18px; }}
  .health {{ display:flex; align-items:center; gap:8px; margin:4px 0 10px; font-size:0.92rem; }}
  .health .dot {{ width:9px; height:9px; border-radius:50%; flex-shrink:0; }}
  .health.ok .dot {{ background:var(--teal-700); }}
  .health.warn .dot {{ background:var(--amber-dark); }}
  .health.bad .dot {{ background:var(--rose); }}
  .counts {{ margin:0 0 12px; font-size:0.88rem; color:#39434d; font-variant-numeric:tabular-nums; }}
  .langbar {{ display:flex; height:9px; border-radius:5px; overflow:hidden; background:var(--border); margin:4px 0 6px; }}
  .langbar .seg:nth-child(1){{background:#3fb3a1;}} .langbar .seg:nth-child(2){{background:#5b8def;}}
  .langbar .seg:nth-child(3){{background:#e0a33a;}} .langbar .seg:nth-child(4){{background:#b06fd6;}}
  .langbar .seg:nth-child(n+5){{background:#8aa0a8;}}
  .legend {{ margin:0 0 12px; font-size:0.78rem; color:var(--muted); display:flex; flex-wrap:wrap; gap:4px 12px; }}
  ul.checks {{ list-style:none; margin:0 0 10px; padding:0; display:flex; flex-wrap:wrap; gap:6px 14px; font-size:0.84rem; font-family:'DM Mono',monospace; }}
  ul.checks .yes {{ color:var(--teal-700); }} ul.checks .no {{ color:var(--muted); }}
  .implements {{ margin:8px 0 0; font-size:0.85rem; }}
  .spec-chip {{ display:inline-block; font-family:'DM Mono',monospace; font-size:0.78rem; background:var(--teal-50); color:var(--teal-700); padding:2px 8px; border-radius:999px; text-decoration:none; margin:2px 3px 0 0; }}
  .spec-chip:hover {{ text-decoration:underline; }}
</style>
</head>
<body>
  <div class="wrap">
    <a class="back" href="../index.html#catalog">&#8592; Back to catalog</a>
    <h1>{esc(name)} {badge}</h1>
    <p class="desc">{esc(desc)}</p>
    <div class="links">{''.join(links)}</div>
    {judgement_block}
    {repo_block}
    {lineage}
    {history_block}
    <footer>MACH — Machine-Actionable Catalog for Healthcare · Judgement is rule-based, derived from harvested signals · <a href="../index.html">machcatalog.org</a></footer>
  </div>
</body>
</html>
"""


def main() -> int:
    signals = load_signals()
    entries = load_entries()
    OUT_DIR.mkdir(exist_ok=True)

    written = 0
    for ident, entry in entries.items():
        page = render_page(entry, signals.get(ident, {}))
        (OUT_DIR / f"{ident}.html").write_text(page, encoding="utf-8")
        written += 1

    print(f"Wrote {written} entry detail pages to {OUT_DIR}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
