#!/usr/bin/env python3
"""
generate_dashboard.py
Builds mach-dashboard.html from the live catalogue in entries/*.jsonld.

Every number — KPIs, charts, insight prose — is computed from the entries at
run time, so the dashboard never goes stale. Run locally or via CI alongside
generate_entries.py. No hand-maintained figures.
"""

import json
import sys
from collections import Counter
from datetime import date
from pathlib import Path

ENTRIES_DIR = Path("entries")
OUT_HTML    = Path("mach-dashboard.html")

sys.path.insert(0, str(Path(__file__).parent))
from taxonomy import label as category_label  # canonical category display names

# ── Load ────────────────────────────────────────────────────────────────────
def load_entries():
    entries = []
    for path in sorted(ENTRIES_DIR.rglob("*.jsonld")):
        if path.name.startswith("_"):
            continue
        try:
            entries.append(json.loads(path.read_text(encoding="utf-8")))
        except json.JSONDecodeError as e:
            print(f"WARN: skipping {path} — {e}")
    return entries

def as_list(v):
    if v is None:
        return []
    return v if isinstance(v, list) else [v]

def license_short(lic):
    if not isinstance(lic, str) or not lic:
        return "unknown"
    return lic.rstrip("/").split("/")[-1] if lic.startswith("http") else lic

# ── Aggregate ───────────────────────────────────────────────────────────────
def aggregate(entries):
    total = len(entries)
    cat   = Counter()        # canonical category label -> count
    gov   = Counter()
    mat   = Counter()
    judg  = Counter()
    lic   = Counter()
    lang  = Counter()
    deploy = Counter()
    os_    = Counter()
    domain = Counter()
    kw     = Counter()
    # judgement within each category, for the stacked bar
    judg_by_cat = {}

    for e in entries:
        c = category_label(e.get("mach:category", "")) or "Other"
        cat[c] += 1

        g = e.get("mach:governance")
        if g: gov[g] += 1
        m = e.get("mach:maturity")
        if m: mat[m] += 1
        j = e.get("mach:judgement")
        if j:
            judg[j] += 1
            judg_by_cat.setdefault(c, Counter())[j] += 1

        lic[license_short(e.get("license", ""))] += 1

        for l in as_list(e.get("programmingLanguage")):
            lang[l] += 1
        for d in as_list(e.get("mach:deploymentContext")):
            deploy[d] += 1
        for o in as_list(e.get("operatingSystem")):
            os_[o] += 1
        for d in as_list(e.get("mach:clinicalDomain")):
            domain[d] += 1
        for k in as_list(e.get("keywords")):
            kw[k] += 1

    return dict(
        total=total, cat=cat, gov=gov, mat=mat, judg=judg, lic=lic,
        lang=lang, deploy=deploy, os=os_, domain=domain, kw=kw,
        judg_by_cat=judg_by_cat,
    )

# ── Helpers for the template ─────────────────────────────────────────────────
TITLE = str.title

def pct(n, total):
    return f"{(100.0 * n / total):.1f}%" if total else "0.0%"

def labelled(counter, n=None):
    """[('Label (count)', count), …] most-common first."""
    items = counter.most_common(n)
    return [f"{k} ({v})" for k, v in items], [v for _, v in items]

def dom_title(s):
    return s.replace("-", " ").title()

# ── Build HTML ───────────────────────────────────────────────────────────────
def build_html(a):
    total = a["total"]
    judg  = a["judg"]
    cat   = a["cat"]
    today = date.today().strftime("%B %Y")

    software_n = cat.get(category_label("software"), 0)
    models_n   = cat.get(category_label("ai-ml-models"), 0) + cat.get(category_label("models"), 0)

    # Category doughnut
    cat_labels, cat_data = labelled(cat)

    # Governance doughnut
    gov_labels, gov_data = labelled(a["gov"])

    # Maturity doughnut (fixed order where present)
    mat_order = ["production", "beta", "experimental", "legacy"]
    mat_labels, mat_data = [], []
    for m in mat_order:
        if a["mat"].get(m):
            mat_labels.append(f"{TITLE(m)} ({a['mat'][m]})")
            mat_data.append(a["mat"][m])

    # Licence (top 8) horizontal bar
    lic_labels, lic_data = labelled(a["lic"], 8)
    lic_labels = [s.split(" (")[0] for s in lic_labels]  # bar: name only

    # Languages (top 8)
    lang_labels, lang_data = labelled(a["lang"], 8)
    lang_labels = [s.split(" (")[0] for s in lang_labels]

    # Deployment doughnut
    dep_labels, dep_data = labelled(a["deploy"])

    # OS bar
    os_labels, os_data = labelled(a["os"], 8)
    os_labels = [s.split(" (")[0] for s in os_labels]

    # Judgement-by-category stacked bar (categories that have any judgement)
    jbc = a["judg_by_cat"]
    jbc_cats = [c for c, _ in cat.most_common() if c in jbc]
    adopt_d  = [jbc.get(c, {}).get("Adopt", 0)   for c in jbc_cats]
    assess_d = [jbc.get(c, {}).get("Assess", 0)  for c in jbc_cats]
    caut_d   = [jbc.get(c, {}).get("Caution", 0) for c in jbc_cats]

    # Clinical domain bars (top 15)
    domains = a["domain"].most_common(15)
    dom_rows = [(dom_title(k), v) for k, v in domains]

    # Keywords (top 20)
    kws = a["kw"].most_common(20)

    # ── Insight prose, all derived from the numbers ──
    top_gov = a["gov"].most_common(1)[0] if a["gov"] else ("—", 0)
    vendor_n = a["gov"].get("vendor-led", 0)
    top_dom = domains[0] if domains else ("—", 0)
    top_lic = a["lic"].most_common(1)[0] if a["lic"] else ("—", 0)
    mit_n = a["lic"].get("MIT", 0)
    gpl_n = a["lic"].get("GPL-3.0", 0)
    py_n = a["lang"].get("Python", 0)
    lang_total = sum(a["lang"].values())
    prod_n = a["mat"].get("production", 0)
    fhir_n = a["kw"].get("fhir", 0)
    interop_n = a["kw"].get("interoperability", 0)
    self_n = a["deploy"].get("self-hosted", 0)
    cloud_only_n = a["deploy"].get("cloud-only", 0)

    insights = [
        f"<strong>{TITLE(top_gov[0])} governance leads:</strong> {top_gov[0]} accounts for "
        f"{top_gov[1]} of {total} entries ({pct(top_gov[1], total)}) — reflecting the "
        f"research-first origins of open-source healthcare tooling. {vendor_n} are vendor-led.",

        f"<strong>{dom_title(top_dom[0])} is the most represented clinical domain</strong> "
        f"with {top_dom[1]} entries.",

        f"<strong>{top_lic[0]} is the dominant licence</strong> ({top_lic[1]} entries, "
        f"{pct(top_lic[1], total)}). MIT follows at {mit_n}. Only {gpl_n} entries use "
        f"copyleft (GPL-3.0), reducing commercial-adoption friction.",

        f"<strong>Python dominates healthcare AI tooling:</strong> {py_n} of {lang_total} "
        f"declared-language mentions are Python "
        f"({pct(py_n, lang_total)}).",

        f"<strong>Production maturity is the norm:</strong> {prod_n} of {total} entries "
        f"({pct(prod_n, total)}) are rated production — MACH deliberately excludes "
        f"prototype-only tools, so this reflects curation, not field-wide maturity.",

        f"<strong>FHIR adoption is real but not dominant:</strong> {fhir_n} entries carry "
        f"the \"fhir\" keyword; interoperability remains a gap "
        f"({interop_n} tagged \"interoperability\").",

        f"<strong>Self-hosted deployment dominates ({self_n} entries):</strong> healthcare "
        f"data-sovereignty concerns drive on-premise preference; only {cloud_only_n} are "
        f"cloud-only.",
    ]
    insight_html = "\n  ".join(
        f'<div class="insight-item">— {s}</div>' for s in insights
    )

    cats_count = len([c for c in cat if cat[c]])

    def js(x):
        return json.dumps(x)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>MACH Catalog Intelligence Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ background: #0d1117; color: #e6edf3; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }}
  .header {{ text-align: center; padding: 40px 20px 20px; background: linear-gradient(180deg, #161b22 0%, #0d1117 100%); border-bottom: 1px solid #21262d; }}
  .header h1 {{ font-size: 2.2rem; font-weight: 700; }}
  .header h1 span {{ color: #58a6ff; }}
  .header p {{ color: #8b949e; margin-top: 8px; font-size: 0.95rem; }}
  .badges {{ display: flex; flex-wrap: wrap; justify-content: center; gap: 10px; margin-top: 16px; }}
  .badge {{ background: #21262d; border: 1px solid #30363d; border-radius: 20px; padding: 5px 14px; font-size: 0.8rem; color: #8b949e; }}
  .kpi-grid {{ display: grid; grid-template-columns: repeat(6, 1fr); gap: 12px; padding: 24px 32px; }}
  .kpi {{ background: #161b22; border: 1px solid #21262d; border-radius: 10px; padding: 20px 16px; text-align: center; }}
  .kpi .num {{ font-size: 2rem; font-weight: 700; }}
  .kpi .label {{ font-size: 0.75rem; color: #8b949e; margin-top: 4px; text-transform: uppercase; letter-spacing: 0.05em; }}
  .insights {{ margin: 0 32px 24px; background: #161b22; border: 1px solid #21262d; border-radius: 10px; padding: 20px 24px; }}
  .insights h3 {{ color: #58a6ff; font-size: 0.85rem; margin-bottom: 12px; text-transform: uppercase; letter-spacing: 0.08em; }}
  .insight-item {{ color: #c9d1d9; font-size: 0.88rem; line-height: 1.6; padding: 4px 0; border-bottom: 1px solid #21262d; }}
  .insight-item:last-child {{ border-bottom: none; }}
  .insight-item strong {{ color: #f0f6fc; }}
  .section {{ padding: 0 32px 32px; }}
  .section-title {{ font-size: 1rem; font-weight: 600; color: #f0f6fc; margin-bottom: 16px; padding-bottom: 8px; border-bottom: 1px solid #21262d; }}
  .section-title span {{ color: #58a6ff; }}
  .chart-grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }}
  .chart-grid-3 {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 16px; }}
  .chart-box {{ background: #161b22; border: 1px solid #21262d; border-radius: 10px; padding: 20px; }}
  .chart-box h4 {{ font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.08em; color: #8b949e; margin-bottom: 16px; }}
  .chart-box canvas {{ max-height: 240px; }}
  .bar-list {{ display: flex; flex-direction: column; gap: 8px; }}
  .bar-item {{ display: flex; align-items: center; gap: 10px; font-size: 0.82rem; }}
  .bar-item .name {{ width: 140px; flex-shrink: 0; color: #c9d1d9; text-align: right; font-size: 0.78rem; }}
  .bar-item .bar-wrap {{ flex: 1; background: #21262d; border-radius: 3px; height: 18px; position: relative; }}
  .bar-item .bar-fill {{ height: 100%; border-radius: 3px; }}
  .bar-item .val {{ width: 36px; text-align: right; color: #8b949e; font-size: 0.78rem; flex-shrink: 0; }}
  .note {{ font-size: 0.78rem; color: #58a6ff; margin-top: 12px; padding: 8px 12px; background: #0d2137; border-left: 3px solid #58a6ff; border-radius: 0 6px 6px 0; }}
  .judgement-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 16px; }}
  .judgement-card {{ border-radius: 10px; padding: 18px; text-align: center; }}
  .judgement-card.adopt {{ background: #0d2b1a; border: 1px solid #2ea043; }}
  .judgement-card.assess {{ background: #1a1a0d; border: 1px solid #d29922; }}
  .judgement-card.caution {{ background: #2b0d0d; border: 1px solid #da3633; }}
  .judgement-card .num {{ font-size: 2.2rem; font-weight: 700; }}
  .judgement-card.adopt .num {{ color: #3fb950; }}
  .judgement-card.assess .num {{ color: #e3b341; }}
  .judgement-card.caution .num {{ color: #f85149; }}
  .judgement-card .label {{ font-size: 0.8rem; color: #8b949e; margin-top: 4px; }}
  .judgement-card .pct {{ font-size: 0.75rem; color: #6e7681; margin-top: 2px; }}
  footer {{ text-align: center; padding: 24px; color: #6e7681; font-size: 0.78rem; border-top: 1px solid #21262d; margin-top: 16px; }}
</style>
</head>
<body>

<div class="header">
  <h1>MACH <span>Catalog Intelligence</span> Dashboard</h1>
  <p>Machine-Actionable Catalog for Healthcare · Open-source tools, models, datasets, and standards</p>
  <div class="badges">
    <span class="badge">{total} Entries Analysed</span>
    <span class="badge">{cats_count} Entry Categories</span>
    <span class="badge">{len(a['domain'])} Clinical Domains</span>
    <span class="badge">Verified Metadata · CC-BY-4.0</span>
    <span class="badge">Generated: {today}</span>
  </div>
</div>

<!-- KPI Row -->
<div class="kpi-grid">
  <div class="kpi"><div class="num" style="color:#58a6ff">{total}</div><div class="label">Total Entries</div></div>
  <div class="kpi"><div class="num" style="color:#3fb950">{judg.get('Adopt',0)}</div><div class="label">Adopt</div></div>
  <div class="kpi"><div class="num" style="color:#e3b341">{judg.get('Assess',0)}</div><div class="label">Assess</div></div>
  <div class="kpi"><div class="num" style="color:#f85149">{judg.get('Caution',0)}</div><div class="label">Caution</div></div>
  <div class="kpi"><div class="num" style="color:#a371f7">{software_n}</div><div class="label">Software Tools</div></div>
  <div class="kpi"><div class="num" style="color:#f78166">{models_n}</div><div class="label">AI/ML Models</div></div>
</div>

<!-- Intelligence Findings -->
<div class="insights">
  <h3>🔍 Top Intelligence Findings from {total} MACH Entries</h3>
  {insight_html}
</div>

<!-- Judgement Section -->
<div class="section">
  <div class="section-title">Editorial Judgement Distribution — <span>What MACH Recommends</span></div>
  <div class="judgement-grid">
    <div class="judgement-card adopt"><div class="num">{judg.get('Adopt',0)}</div><div class="label">Adopt</div><div class="pct">{pct(judg.get('Adopt',0), total)} of catalog</div></div>
    <div class="judgement-card assess"><div class="num">{judg.get('Assess',0)}</div><div class="label">Assess</div><div class="pct">{pct(judg.get('Assess',0), total)} of catalog</div></div>
    <div class="judgement-card caution"><div class="num">{judg.get('Caution',0)}</div><div class="label">Caution</div><div class="pct">{pct(judg.get('Caution',0), total)} of catalog</div></div>
  </div>
  <div class="chart-grid-2">
    <div class="chart-box"><h4>Entries by Category</h4><canvas id="catChart"></canvas></div>
    <div class="chart-box"><h4>Judgement by Category</h4><canvas id="judgCatChart"></canvas></div>
  </div>
</div>

<!-- Governance & Maturity -->
<div class="section">
  <div class="section-title">Governance &amp; Maturity — <span>Who Builds Healthcare Open Source</span></div>
  <div class="chart-grid-3">
    <div class="chart-box"><h4>Governance Model</h4><canvas id="govChart"></canvas></div>
    <div class="chart-box"><h4>Maturity Level</h4><canvas id="matChart"></canvas></div>
    <div class="chart-box"><h4>Licence Landscape (Top 8)</h4><canvas id="licChart"></canvas></div>
  </div>
</div>

<!-- Clinical Domain -->
<div class="section">
  <div class="section-title">Clinical Domain Coverage — <span>Where Open Source Exists</span></div>
  <div class="chart-grid-2">
    <div class="chart-box" style="grid-column: span 2">
      <h4>Entries by Clinical Domain (Top 15)</h4>
      <div class="bar-list" id="domainBars"></div>
    </div>
  </div>
</div>

<!-- Tech Stack -->
<div class="section">
  <div class="section-title">Technology Landscape — <span>Languages &amp; Deployment</span></div>
  <div class="chart-grid-3">
    <div class="chart-box"><h4>Programming Languages</h4><canvas id="langChart"></canvas></div>
    <div class="chart-box"><h4>Deployment Context</h4><canvas id="deployChart"></canvas></div>
    <div class="chart-box"><h4>Operating System Support</h4><canvas id="osChart"></canvas></div>
  </div>
</div>

<!-- Keywords -->
<div class="section">
  <div class="section-title">Top Keywords — <span>What Healthcare Open Source Is About</span></div>
  <div class="chart-box">
    <h4>Most Frequent Keywords (Top 20)</h4>
    <div class="bar-list" id="kwBars"></div>
  </div>
</div>

<footer>
  MACH — Machine-Actionable Catalog for Healthcare · github.com/FORSE-H/MACH · Apache-2.0 / CC-BY-4.0 · All statistics derived from verified catalog entries · {today}
</footer>

<script>
const COLORS = ['#58a6ff','#3fb950','#e3b341','#f85149','#a371f7','#f78166','#56d364','#ffa657','#79c0ff','#ffb3c8'];
const GRID = {{ color: '#21262d' }};
const TICK = {{ color: '#8b949e', font: {{ size: 11 }} }};

new Chart(document.getElementById('catChart'), {{
  type: 'doughnut',
  data: {{ labels: {js(cat_labels)}, datasets: [{{ data: {js(cat_data)}, backgroundColor: COLORS, borderWidth: 2, borderColor: '#161b22' }}] }},
  options: {{ plugins: {{ legend: {{ labels: {{ color: '#8b949e', font: {{ size: 11 }}, boxWidth: 12 }} }} }}, cutout: '60%' }}
}});

new Chart(document.getElementById('judgCatChart'), {{
  type: 'bar',
  data: {{ labels: {js(jbc_cats)}, datasets: [
    {{ label: 'Adopt', data: {js(adopt_d)}, backgroundColor: '#2ea043' }},
    {{ label: 'Assess', data: {js(assess_d)}, backgroundColor: '#d29922' }},
    {{ label: 'Caution', data: {js(caut_d)}, backgroundColor: '#da3633' }}
  ] }},
  options: {{ scales: {{ x: {{ stacked: true, ticks: TICK, grid: GRID }}, y: {{ stacked: true, ticks: TICK, grid: GRID }} }},
    plugins: {{ legend: {{ labels: {{ color: '#8b949e', font: {{ size: 11 }}, boxWidth: 12 }} }} }} }}
}});

new Chart(document.getElementById('govChart'), {{
  type: 'doughnut',
  data: {{ labels: {js(gov_labels)}, datasets: [{{ data: {js(gov_data)}, backgroundColor: COLORS, borderWidth: 2, borderColor: '#161b22' }}] }},
  options: {{ plugins: {{ legend: {{ labels: {{ color: '#8b949e', font: {{ size: 10 }}, boxWidth: 12 }} }} }}, cutout: '60%' }}
}});

new Chart(document.getElementById('matChart'), {{
  type: 'doughnut',
  data: {{ labels: {js(mat_labels)}, datasets: [{{ data: {js(mat_data)}, backgroundColor: ['#3fb950','#e3b341','#f85149','#6e7681'], borderWidth: 2, borderColor: '#161b22' }}] }},
  options: {{ plugins: {{ legend: {{ labels: {{ color: '#8b949e', font: {{ size: 11 }}, boxWidth: 12 }} }} }}, cutout: '60%' }}
}});

new Chart(document.getElementById('licChart'), {{
  type: 'bar',
  data: {{ labels: {js(lic_labels)}, datasets: [{{ data: {js(lic_data)}, backgroundColor: COLORS }}] }},
  options: {{ indexAxis: 'y', scales: {{ x: {{ ticks: TICK, grid: GRID }}, y: {{ ticks: TICK, grid: GRID }} }}, plugins: {{ legend: {{ display: false }} }} }}
}});

new Chart(document.getElementById('langChart'), {{
  type: 'bar',
  data: {{ labels: {js(lang_labels)}, datasets: [{{ data: {js(lang_data)}, backgroundColor: '#58a6ff' }}] }},
  options: {{ indexAxis: 'y', scales: {{ x: {{ ticks: TICK, grid: GRID }}, y: {{ ticks: {{ ...TICK, font: {{ size: 10 }} }}, grid: GRID }} }}, plugins: {{ legend: {{ display: false }} }} }}
}});

new Chart(document.getElementById('deployChart'), {{
  type: 'doughnut',
  data: {{ labels: {js(dep_labels)}, datasets: [{{ data: {js(dep_data)}, backgroundColor: COLORS, borderWidth: 2, borderColor: '#161b22' }}] }},
  options: {{ plugins: {{ legend: {{ labels: {{ color: '#8b949e', font: {{ size: 10 }}, boxWidth: 12 }} }} }}, cutout: '60%' }}
}});

new Chart(document.getElementById('osChart'), {{
  type: 'bar',
  data: {{ labels: {js(os_labels)}, datasets: [{{ data: {js(os_data)}, backgroundColor: '#a371f7' }}] }},
  options: {{ scales: {{ x: {{ ticks: TICK, grid: GRID }}, y: {{ ticks: TICK, grid: GRID }} }}, plugins: {{ legend: {{ display: false }} }} }}
}});

const domains = {js(dom_rows)};
const domColors = ['#58a6ff','#f85149','#3fb950','#e3b341','#a371f7','#f78166','#56d364','#ffa657','#79c0ff','#58a6ff','#3fb950','#e3b341','#a371f7','#f78166','#56d364'];
const maxD = domains.length ? domains[0][1] : 1;
const domContainer = document.getElementById('domainBars');
domains.forEach(([name, val], i) => {{
  domContainer.innerHTML += `<div class="bar-item"><div class="name">${{name}}</div><div class="bar-wrap"><div class="bar-fill" style="width:${{(val/maxD*100).toFixed(1)}}%;background:${{domColors[i % domColors.length]}}"></div></div><div class="val">${{val}}</div></div>`;
}});

const keywords = {js(kws)};
const maxK = keywords.length ? keywords[0][1] : 1;
const kwContainer = document.getElementById('kwBars');
keywords.forEach(([name, val], i) => {{
  kwContainer.innerHTML += `<div class="bar-item"><div class="name">${{name}}</div><div class="bar-wrap"><div class="bar-fill" style="width:${{(val/maxK*100).toFixed(1)}}%;background:${{COLORS[i % COLORS.length]}}"></div></div><div class="val">${{val}}</div></div>`;
}});
</script>

</body>
</html>
"""

def main():
    entries = load_entries()
    a = aggregate(entries)
    print(f"Loaded {a['total']} entries")
    OUT_HTML.write_text(build_html(a), encoding="utf-8")
    print(f"Wrote {OUT_HTML} — {a['total']} entries, "
          f"{len(a['cat'])} categories, {len(a['domain'])} clinical domains")

if __name__ == "__main__":
    main()
