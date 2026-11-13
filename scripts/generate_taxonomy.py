#!/usr/bin/env python3
"""generate_taxonomy.py — build taxonomy.html from the live catalogue.

A browsable, data-derived view of MACH's multi-axis taxonomy: Type (category) ->
Function (subcategory) with live counts and the entries in each, plus the Domain
and Standards facets. Regenerated in CI from entries/ + categories.yaml, so it
never drifts from the catalogue.
"""
from __future__ import annotations

import html
import json
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

import yaml

ENTRIES_DIR = Path("entries")
TAXONOMY = Path("data/taxonomy/categories.yaml")
OUT_HTML = Path("taxonomy.html")


def esc(s) -> str:
    return html.escape(str(s)) if s is not None else ""


def load():
    tax = yaml.safe_load(TAXONOMY.read_text(encoding="utf-8"))
    entries = []
    for p in sorted(ENTRIES_DIR.rglob("*.jsonld")):
        if p.name.startswith("_"):
            continue
        d = json.loads(p.read_text(encoding="utf-8"))
        entries.append(d)
    return tax, entries


def build(tax, entries) -> str:
    cat_label = {c["id"]: c["name"] for c in tax["categories"]}
    func_label = {}
    for c in tax["categories"]:
        for fn in c.get("functions", []):
            func_label[(c["id"], fn["id"])] = fn["name"]

    # counts
    by_cat_func = defaultdict(Counter)
    func_entries = defaultdict(list)
    domain = Counter()
    byline = Counter()
    standards = 0
    for d in entries:
        c = d.get("mach:category")
        f = d.get("mach:subcategory")
        by_cat_func[c][f] += 1
        func_entries[(c, f)].append((d.get("identifier"), d.get("name")))
        byline[d.get("mach:subcategoryBy", "existing")] += 1
        for dm in (d.get("mach:clinicalDomain") or []):
            domain[dm] += 1
        if d.get("mach:supportsSpec"):
            standards += 1

    total = len(entries)
    rule_n = byline.get("rule:keyword", 0) + byline.get("rule:spec", 0) + byline.get("catalog", 0)
    today = date.today().strftime("%B %Y")

    # ── Type > Function sections ──
    sections = []
    for c in tax["categories"]:
        cid = c["id"]
        funcs = by_cat_func.get(cid, {})
        cat_total = sum(funcs.values())
        rows = []
        for fn in c.get("functions", []):
            fid = fn["id"]
            n = funcs.get(fid, 0)
            ids = func_entries.get((cid, fid), [])
            sample = ", ".join(esc(nm or i) for i, nm in ids[:8]) + (" …" if len(ids) > 8 else "")
            opacity = "" if n else ' class="empty"'
            rows.append(
                f'<tr{opacity}><td class="fn">{esc(fn["name"])} '
                f'<code>{esc(fid)}</code></td><td class="n">{n}</td>'
                f'<td class="ex">{sample}</td></tr>'
            )
        sections.append(f"""
    <section class="cat">
      <h2>{esc(c["name"])} <span class="ct">{cat_total}</span></h2>
      <p class="cd">{esc(c.get("description",""))}</p>
      <table>
        <thead><tr><th>Function</th><th>n</th><th>entries</th></tr></thead>
        <tbody>{''.join(rows)}</tbody>
      </table>
    </section>""")

    # ── Domain facet (top 20) ──
    dom_rows = "".join(
        f'<tr><td>{esc(k)}</td><td class="n">{v}</td></tr>'
        for k, v in domain.most_common(20)
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>MACH Taxonomy</title>
<style>
  :root {{
    --bg:#f7f9f8; --surface:#fff; --ink:#11201b; --muted:#5a6b64; --line:#dde6e2;
    --teal:#0f6e56; --teal-bright:#1d9e75; --teal-tint:#e4f3ee;
    --display:'Fraunces',Georgia,serif; --body:'Inter',-apple-system,'Segoe UI',system-ui,sans-serif; --mono:'DM Mono',ui-monospace,monospace;
  }}
  @media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{
    --bg:#0e1613;--surface:#142019;--ink:#e7efea;--muted:#9db3aa;--line:#25352d;
    --teal:#4fc3a1;--teal-bright:#6fd9ba;--teal-tint:#15271f;color-scheme:dark;}}}}
  :root[data-theme="dark"]{{
    --bg:#0e1613;--surface:#142019;--ink:#e7efea;--muted:#9db3aa;--line:#25352d;
    --teal:#4fc3a1;--teal-bright:#6fd9ba;--teal-tint:#15271f;color-scheme:dark;}}
  * {{ box-sizing:border-box; }}
  body {{ background:var(--bg); color:var(--ink); font-family:var(--body); line-height:1.5; margin:0; }}
  .wrap {{ max-width:900px; margin:0 auto; padding:32px 16px 56px; }}
  header {{ border-bottom:3px solid var(--teal); padding-bottom:16px; margin-bottom:8px; }}
  h1 {{ font-family:var(--display); font-weight:600; font-size:2rem; margin:0; letter-spacing:-0.01em; }}
  h1 span {{ color:var(--teal); }}
  .sub {{ color:var(--muted); font-size:0.9rem; margin-top:4px; }}
  .lede {{ color:var(--muted); font-size:0.92rem; max-width:72ch; margin:16px 0 20px; }}
  .lede b {{ color:var(--ink); }}
  .axes {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:10px; margin-bottom:12px; }}
  .axis {{ background:var(--surface); border:1px solid var(--line); border-top:3px solid var(--teal); border-radius:10px; padding:12px 14px; }}
  .axis .e {{ font-size:0.64rem; text-transform:uppercase; letter-spacing:0.08em; color:var(--teal); font-weight:700; }}
  .axis h3 {{ margin:2px 0 2px; font-family:var(--display); font-size:0.98rem; }}
  .axis code {{ font-family:var(--mono); font-size:0.74rem; color:var(--muted); }}
  .prov {{ background:var(--teal-tint); border:1px solid var(--line); border-radius:10px; padding:12px 16px; font-size:0.86rem; margin:14px 0 26px; }}
  .prov b {{ color:var(--teal); }}
  section.cat {{ margin:30px 0; }}
  h2 {{ font-family:var(--display); font-weight:600; font-size:1.35rem; margin:0 0 2px; }}
  h2 .ct {{ font-size:0.9rem; color:var(--muted); font-weight:400; }}
  .cd {{ color:var(--muted); font-size:0.85rem; margin:0 0 10px; }}
  table {{ width:100%; border-collapse:collapse; font-size:0.86rem; border:1px solid var(--line); border-radius:10px; overflow:hidden; }}
  th,td {{ text-align:left; padding:8px 11px; border-bottom:1px solid var(--line); vertical-align:top; }}
  th {{ background:var(--teal-tint); color:var(--teal); font-size:0.68rem; text-transform:uppercase; letter-spacing:0.06em; font-weight:700; }}
  tr:last-child td {{ border-bottom:none; }}
  tr.empty {{ opacity:0.45; }}
  td.fn {{ font-weight:500; white-space:nowrap; }}
  td.fn code {{ font-family:var(--mono); font-size:0.74rem; color:var(--muted); font-weight:400; display:block; }}
  td.n {{ font-variant-numeric:tabular-nums; color:var(--muted); text-align:right; width:40px; }}
  td.ex {{ color:var(--muted); font-size:0.82rem; }}
  footer {{ margin-top:40px; padding-top:16px; border-top:1px solid var(--line); font-size:0.78rem; color:var(--muted); }}
  footer a {{ color:var(--teal); }}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>MACH <span>Taxonomy</span></h1>
    <div class="sub">A multi-axis, EDAM-inspired classification · {total} entries · {today}</div>
  </header>

  <p class="lede">Every entry is classified on four orthogonal axes. <b>Type</b> is the top-level category (from the entry's folder). <b>Function</b> is a controlled sub-type, assigned by published deterministic rules or an explicit curator decision. <b>Domain</b> is the clinical area, and <b>Standards</b> are the specifications a tool implements.</p>

  <div class="axes">
    <div class="axis"><div class="e">EDAM · Data</div><h3>Type</h3><code>mach:category</code></div>
    <div class="axis"><div class="e">EDAM · Operation</div><h3>Function</h3><code>mach:subcategory</code></div>
    <div class="axis"><div class="e">EDAM · Topic</div><h3>Domain</h3><code>mach:clinicalDomain</code></div>
    <div class="axis"><div class="e">EDAM · Format</div><h3>Standards</h3><code>mach:supportsSpec</code></div>
  </div>

  <div class="prov">
    Function is assigned deterministically where a signal is clear: <b>{rule_n}</b> by rule
    (from harvested keywords / implemented standards), <b>{byline.get('curator',0)}</b> by curator decision,
    <b>{byline.get('existing',0)}</b> authored (AI tooling). Each entry records how it was classified
    (<code>mach:subcategoryBy</code>), so the taxonomy is auditable, not opinion.
  </div>
{''.join(sections)}

    <section class="cat">
      <h2>Domain <span class="ct">top 20 of {len(domain)}</span></h2>
      <p class="cd">Clinical and scientific areas (an entry may have several).</p>
      <table><thead><tr><th>Domain</th><th>n</th></tr></thead><tbody>{dom_rows}</tbody></table>
    </section>

  <footer>
    MACH — Machine-Actionable Catalog for Healthcare · taxonomy derived from {total} entries, regenerated in CI ·
    model inspired by <a href="https://edamontology.org/" target="_blank" rel="noopener">EDAM</a> ·
    <a href="index.html">machcatalog.org</a>
  </footer>
</div>
</body>
</html>
"""


def main() -> int:
    tax, entries = load()
    OUT_HTML.write_text(build(tax, entries), encoding="utf-8")
    print(f"Wrote {OUT_HTML} — {len(entries)} entries")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
