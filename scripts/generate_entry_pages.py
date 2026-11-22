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


def _impact_section(signals: dict) -> str:
    """Academic impact from OpenAlex (citations), shown only for entries that
    carry a DOI and were found in OpenAlex. Returns '' when there's nothing."""
    citations = signals.get("citations")
    if citations in (None, ""):
        return ""
    try:
        n = int(citations)
    except (TypeError, ValueError):
        return ""
    year = signals.get("publication_year")
    venue = signals.get("openalex_venue")

    bits = [f"&#10078; <strong>{n:,}</strong> citation{'' if n == 1 else 's'}"]
    meta = []
    if venue:
        meta.append(esc(venue))
    if year:
        meta.append(esc(year))
    tail = f'<span class="muted"> — {" · ".join(meta)}</span>' if meta else ""

    return (
        '<section class="repo">\n    <h3>Academic impact</h3>\n'
        f'    <p class="counts">{bits[0]}{tail}</p>\n'
        '    <p class="muted" style="font-size:0.8rem;margin:0;">Citation count from '
        '<a href="https://openalex.org" target="_blank" rel="noopener">OpenAlex</a>, '
        "matched by the entry&rsquo;s DOI. A measure of reach, not quality.</p>\n    </section>"
    )


def _security_section(signals: dict) -> str:
    """Security posture: OpenSSF Scorecard (repo hygiene, 0–10) and OSV known
    vulnerabilities. Shown only when at least one was harvested. Hygiene is not
    a safety guarantee — the note says so."""
    score = signals.get("ssf_score")
    vulns = signals.get("osv_known_vulns")
    has_score = score not in (None, "")
    has_vulns = vulns not in (None, "")
    if not (has_score or has_vulns):
        return ""

    parts = ['<section class="repo">', "<h3>Security posture</h3>", '<p class="counts">']
    chips = []
    if has_score:
        try:
            s = float(score)
            cls = "ok" if s >= 7 else ("warn" if s >= 4 else "bad")
        except (TypeError, ValueError):
            s, cls = score, "warn"
        chips.append(
            f'<span class="ssf {cls}">OpenSSF Scorecard: <strong>{esc(s)}</strong>/10</span>'
        )
    if has_vulns:
        try:
            v = int(vulns)
        except (TypeError, ValueError):
            v = vulns
        vcls = "ok" if v == 0 else "bad"
        label = "no known vulnerabilities" if v == 0 else f"{v:,} known vulnerabilit{'y' if v == 1 else 'ies'}"
        chips.append(f'<span class="ssf {vcls}">OSV: <strong>{esc(label)}</strong></span>')
    parts.append(" &nbsp; ".join(chips))
    parts.append("</p>")
    parts.append(
        '<p class="muted" style="font-size:0.8rem;margin:0;">'
        '<a href="https://securityscorecards.dev" target="_blank" rel="noopener">OpenSSF Scorecard</a> '
        "measures a repository&rsquo;s security <em>hygiene</em> (branch protection, code review, "
        "dangerous workflows), and "
        '<a href="https://osv.dev" target="_blank" rel="noopener">OSV</a> lists known published '
        "advisories in discovered packages. Neither certifies that the software is safe to deploy "
        "clinically — they describe the development process, not clinical fitness.</p>"
    )
    parts.append("</section>")
    return "\n    ".join(parts)


def _stem_license(s: str) -> str:
    """Fold SPDX precision suffixes so GPL-2.0-only == GPL-2.0, case-insensitive,
    matching scripts/audit_licenses.py so the page and the audit never disagree
    about what counts as 'the same licence'."""
    s = (s or "").strip().casefold()
    for suf in ("-or-later", "-only"):
        if s.endswith(suf):
            s = s[: -len(suf)]
    return s


def _license_section(entry: dict, signals: dict) -> str:
    """Curated licence block. The authoritative licence is the one in the entry
    JSON-LD (set or confirmed by a human), NOT the harvested signals.license —
    GitHub's detector often reports the linked *code* repo's licence when the
    entry is really a dataset, model weights, or specification. When the two
    differ, we show the curated value as the headline and, transparently, note
    what the harvester saw and why it differs."""
    curated = entry.get("license")
    if not curated:
        return ""
    verified = bool(entry.get("mach:licenseVerified"))
    note = entry.get("mach:licenseNote") or ""
    lic_url = entry.get("mach:licenseUrl") or ""
    harvested = (signals or {}).get("license") or ""
    differs = harvested and _stem_license(harvested) != _stem_license(curated)

    chip_cls = "lic ok" if verified else "lic"
    label = esc(curated)
    if lic_url:
        label = f'<a href="{esc(lic_url)}" target="_blank" rel="noopener">{esc(curated)}</a>'

    parts = ['<section class="repo">', "<h3>Licence</h3>", '<p class="counts">']
    vtag = ' &nbsp;<span class="lic-verified">&#10003; verified against source</span>' if verified else ""
    parts.append(f'<span class="{chip_cls}">{label}</span>{vtag}')
    parts.append("</p>")
    if note:
        parts.append(f'<p class="muted" style="font-size:0.85rem;margin:0;">{esc(note)}</p>')
    if differs:
        parts.append(
            '<p class="muted" style="font-size:0.8rem;margin:6px 0 0;">'
            f'Automated detection (GitHub) reported <code>{esc(harvested)}</code> for the linked '
            'repository; the value above is the curator-verified licence for this entry.</p>'
        )
    parts.append("</section>")
    return "\n    ".join(parts)


_HARDWARE_NOTE = (
    "Open-source medical hardware: the repository holds device designs, PCBs, "
    "firmware, and build documentation. MACH&rsquo;s rule-based signals (stars, "
    "commit recency, licence, repo health) describe the activity and openness of "
    "this <em>design repository</em> &mdash; not the safety, regulatory clearance, "
    "or clinical fitness of any device built from it. Verify licences (hardware and "
    "software may differ), build quality, and any applicable medical-device "
    "regulation before use."
)


def _hardware_note(entry: dict) -> str:
    """An always-on caveat shown at the bottom of every hardware entry page."""
    if entry.get("mach:category") != "hardware":
        return ""
    return (
        '<aside class="hw-note" role="note">'
        '<strong>About medical-hardware entries</strong>'
        f'<p>{_HARDWARE_NOTE}</p>'
        "</aside>"
    )


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
    impact_block = _impact_section(signals)
    security_block = _security_section(signals)
    license_block = _license_section(entry, signals)
    hardware_note = _hardware_note(entry)

    # The lineage table is built from harvested facts. When the entry carries a
    # curator-verified licence that differs from the harvested one, don't let the
    # table present the harvested value as plain fact — annotate that row so the
    # table agrees with the headline Licence section above.
    _curated_license = entry.get("license")
    _license_verified = bool(entry.get("mach:licenseVerified"))

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
    # A harvested field with no value still records *why* (its fetch_status), so
    # the table stays honest. But a raw code like "not_found" reads as a failure
    # when it usually just means the entry isn't on that platform — so map the
    # statuses to plain phrases. The field is still shown (transparency), just
    # without the alarm.
    _STATUS_PHRASE = {
        "not_found": "not on this platform",
        "error": "not reachable",
        "rate_limited": "not checked (rate-limited)",
        "": "—",
    }
    if facts:
        rows = []
        for f in sorted(facts, key=lambda x: x["field_name"]):
            label = _FIELD_LABELS.get(f["field_name"], f["field_name"])
            val = f["value"]
            status = f.get("fetch_status", "")
            phrase = _STATUS_PHRASE.get(status, status or "—")
            val_disp = esc(val) if val not in (None, "") else f'<span class="muted">{esc(phrase)}</span>'
            source_disp = f'<code>{esc(f.get("source_id","—"))}</code>'
            # Override the harvested licence row when the curated licence differs:
            # keep the harvested value visible (lineage honesty) but mark it
            # superseded, and point at the verified value shown above.
            if (f["field_name"] == "license" and _curated_license
                    and _stem_license(val) != _stem_license(_curated_license)):
                val_disp = (
                    f'<span class="muted" style="text-decoration:line-through;">{esc(val)}</span>'
                    f' &rarr; <strong>{esc(_curated_license)}</strong>'
                    + (' <span class="lic-verified">&#10003;</span>' if _license_verified else '')
                )
                source_disp = f'<code>{esc(f.get("source_id","—"))}</code> &rarr; <code>curator</code>'
            rows.append(
                f'<tr><td class="field">{esc(label)}</td>'
                f'<td class="value">{val_disp}</td>'
                f'<td class="source">{source_disp}</td></tr>'
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
  .ssf {{ display:inline-block; font-size:0.86rem; padding:2px 10px; border-radius:999px; font-variant-numeric:tabular-nums; }}
  .ssf.ok {{ background:var(--teal-50); color:var(--teal-700); }}
  .ssf.warn {{ background:#fdf0dd; color:var(--amber-dark); }}
  .ssf.bad {{ background:#fde5e7; color:var(--rose); }}
  .lic {{ display:inline-block; font-family:'DM Mono',monospace; font-size:0.86rem; padding:2px 10px; border-radius:999px; background:#eef1f4; color:var(--ink); }}
  .lic.ok {{ background:var(--teal-50); color:var(--teal-700); }}
  .lic a {{ color:inherit; text-decoration:underline; }}
  .lic-verified {{ font-size:0.78rem; color:var(--teal-700); font-weight:600; }}
  .implements {{ margin:8px 0 0; font-size:0.85rem; }}
  .spec-chip {{ display:inline-block; font-family:'DM Mono',monospace; font-size:0.78rem; background:var(--teal-50); color:var(--teal-700); padding:2px 8px; border-radius:999px; text-decoration:none; margin:2px 3px 0 0; }}
  .spec-chip:hover {{ text-decoration:underline; }}
  .hw-note {{ margin:20px 0 0; padding:14px 16px; border:1px solid var(--border);
    border-left:3px solid #475569; border-radius:8px; background:#F1F5F9; }}
  .hw-note strong {{ display:block; font-size:0.82rem; letter-spacing:0.02em;
    text-transform:uppercase; color:#334155; margin:0 0 4px; }}
  .hw-note p {{ margin:0; font-size:0.86rem; line-height:1.5; color:#39434d; }}
  @media (prefers-color-scheme: dark) {{
    :root:not([data-theme="light"]) .hw-note {{ background:#1e293b; border-left-color:#64748b; }}
    :root:not([data-theme="light"]) .hw-note strong {{ color:#cbd5e1; }}
    :root:not([data-theme="light"]) .hw-note p {{ color:#cbd5e1; }}
  }}
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
    {license_block}
    {security_block}
    {impact_block}
    {lineage}
    {history_block}
    {hardware_note}
    <footer>MACH — Machine-Actionable Catalog for Healthcare · Judgement is rule-based, derived from harvested signals · <a href="../index.html">machcatalog.org</a></footer>
  </div>
  <!-- Privacy-first analytics (GoatCounter — no cookies, no personal data). -->
  <script data-goatcounter="https://machcatalog.goatcounter.com/count"
          async src="//gc.zgo.at/count.js"></script>
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
