# MACH — Claude Code Context File
> This file is read automatically by Claude Code at the start of every session.
> Keep it updated as the project evolves. Last updated: May 2026.

## What is MACH

**MACH** = Machine-Actionable Catalog for Healthcare
**Org:** FORSE-H (github.com/FORSE-H)
**Repo:** https://github.com/FORSE-H/MACH
**Site:** https://forse-h.github.io/MACH (GitHub Pages, live)
**Owner/Curator:** Priyanka Ojha (ORCID: [fill in])
**License:** Code Apache-2.0 | Data CC-BY-4.0

MACH is an open, machine-actionable catalog of open-source healthcare
software, AI/ML models, clinical standards, datasets, and MCP servers.
Every entry is a structured JSON-LD file. A CI pipeline validates,
enriches, and publishes machine-readable exports on every commit.

---

## Current Status (May 2026)

- [x] Repo structure created and pushed to GitHub
- [x] JSON-LD context defined (`data/context/mach.jsonld`)
- [x] 14-category taxonomy defined (`data/taxonomy/categories.yaml`)
- [x] CI validation pipeline live (`.github/workflows/validate.yml`)
- [x] CI site generator live (`.github/workflows/update-site.yml`)
- [x] Landing page live at forse-h.github.io/MACH
- [x] 13 seed entries curated (see below)
- [x] 
- [ ] Landscape2 integration (Phase 2 — funded work)
- [ ] Python FDP server (Phase 2 — funded work)
- [ ] MLDCAT-AP export generator (Phase 2)
- [ ] CodeMeta export generator (Phase 2)
- [ ] Croissant export generator (Phase 2)
- [ ] 50+ total entries (Phase 2 target)
- [ ] Custom domain (openmach.health or similar)

---

## Seed Entries (13 as of May 2026)

| File | Name | Category | Judgement |
|---|---|---|---|
| `entries/software/openmrs.jsonld` | OpenMRS | clinical-systems | Adopt |
| `entries/software/pyhealth.jsonld` | PyHealth | tooling-infrastructure | Adopt |
| `entries/software/vantage6.jsonld` | vantage6 | tooling-infrastructure | Adopt |
| `entries/software/mitk.jsonld` | MITK | medical-imaging-signals | Adopt |
| `entries/software/kaapana.jsonld` | Kaapana | tooling-infrastructure | Assess |
| `entries/models/clinicalbert.jsonld` | ClinicalBERT | ai-ml-models | Adopt |
| `entries/models/nnunet.jsonld` | nnU-Net | medical-imaging-signals | Adopt |
| `entries/models/nndetection.jsonld` | nnDetection | medical-imaging-signals | Assess |
| `entries/models/tractseg.jsonld` | TractSeg | medical-imaging-signals | Assess |
| `entries/standards/fhir-r4.jsonld` | HL7 FHIR R4 | interoperability-standards | Adopt |
| `entries/standards/openehr.jsonld` | openEHR | interoperability-standards | Adopt |
| `entries/mcp-servers/fhir-mcp-wso2.jsonld` | FHIR MCP (WSO2) | mcp-servers-ai-interfaces | Assess |
| `entries/mcp-servers/omcp.jsonld` | OMCP | mcp-servers-ai-interfaces | Assess |

---

## Repo Structure

```
MACH/
├── CLAUDE.md                    ← YOU ARE HERE
├── README.md
├── LICENSE                      (Apache-2.0 for code)
├── LICENSE-DATA                 (CC-BY-4.0 for entries)
├── CONTRIBUTING.md
├── GOVERNANCE.md
├── SUPPORTERS.md
├── index.html                   (GitHub Pages landing page — auto-updated by CI)
├── entries/
│   ├── software/                (.jsonld files + _template.jsonld)
│   ├── models/                  (.jsonld files + _template.jsonld)
│   ├── standards/               (.jsonld files)
│   ├── mcp-servers/             (.jsonld files + _template.jsonld)
│   └── datasets/                (empty, ready for entries)
├── logos/                       (SVG/PNG logos per entry)
├── data/
│   ├── context/mach.jsonld      (JSON-LD @context for all entries)
│   ├── schema/                  (JSON Schema files — TODO)
│   └── taxonomy/categories.yaml (14 categories, judgements, clinical domains)
├── scripts/
│   └── generate_entries.py      (reads entries/*.jsonld → patches index.html)
├── docs/                        (architecture docs, ADRs)
└── .github/
    ├── workflows/
    │   ├── validate.yml         (runs on every PR touching entries/)
    │   └── update-site.yml      (runs on push to main → updates index.html)
    ├── PULL_REQUEST_TEMPLATE.md
    └── ISSUE_TEMPLATE/
        └── new-entry.yml
```

---

## Architecture Decisions (summary — see docs/adr/ for full records)

### ADR-001: JSON-LD as canonical source of truth
All entries are JSON-LD files in Git. No database at MVP.
Git IS the database. Every change is a commit. SHACL validates on PR.

### ADR-002: Static site for Phase 1, FDP server for Phase 2
Phase 1: GitHub Pages + generate_entries.py script regenerates index.html on CI.
Phase 2: Build a lightweight Python FDP server (FastAPI + RDFLib + Supabase/Neon)
implementing the FAIR Data Point spec (specs.fairdatapoint.org).
The Java reference implementation (FAIRDataTeam/FAIRDataPoint) is buggy and
heavy. The NLeSC Python implementation is 5 years old and unmaintained.
We build our own — this is within open-source funder grant scope.

### ADR-003: landscape2 for interactive landscape view
CNCF landscape2 (github.com/cncf/landscape2) will be used as the rendering
engine for the interactive grid/radar/table views.
An adapter script converts JSON-LD entries → landscape2 YAML.
landscape2 is the UI layer; JSON-LD is the source of truth.

### ADR-004: Multi-standard metadata alignment
Each entry type maps to a primary standard:
- Software → CodeMeta 3.0
- ML Model → MLDCAT-AP 3.0 (EU AI Act aligned)
- Dataset → MLCommons Croissant
- MCP Server → MCP server.json (modelcontextprotocol/registry)
- Standard/Spec → DCAT-AP + custom mach: vocabulary
- The catalog itself → DCAT-AP

### ADR-005: mach: vocabulary for editorial fields
Custom `mach:` prefix for fields not in existing standards:
judgement, judgementReason, maturity, clinicalDomain,
deploymentContext, evidence, evidenceType, etc.
Context defined in data/context/mach.jsonld.

---

## Key Metadata Standards (know these before touching schema code)

| Standard | Version | URL | Used for |
|---|---|---|---|
| MLDCAT-AP | 3.0 | semiceu.github.io/MLDCAT-AP/releases/3.0.0/ | ML models |
| CodeMeta | 3.0 | codemeta.github.io | Software |
| DCAT-AP | 3.0 | semiceu.github.io/DCAT-AP/ | Datasets, catalog |
| Croissant | 1.0 | mlcommons.org/croissant | ML datasets |
| MCP server.json | 2024-11-05 | github.com/modelcontextprotocol/registry | MCP servers |
| Bitol ODPS | 1.0 | github.com/bitol-io/open-data-product-standard | Data products |
| SPDX | 3.0 | spdx.org | License expressions |
| FAIR Data Point spec | latest | specs.fairdatapoint.org | FDP server (Phase 2) |

---

## Entry Validation Rules (enforced by CI validate.yml)

Required fields for ALL entries:
- identifier, name, description, url, license
- mach:category (must match taxonomy)
- mach:judgement (Adopt | Situational | Assess | Caution)
- mach:judgementReason (1–3 sentences)
- mach:editorialReviewedAt (YYYY-MM-DD)
- mach:evidence (at least one item with live URL)

Additional for ML models: weightsLicense, trainingDataSummary, intendedUse
Additional for MCP servers: transport, authMethod

Maturity levels: experimental | beta | production | legacy
Governance types: foundation | vendor-led | individual | government | academic | community

---

## Phase 2 Build Plan (funded work)

Priority order for Claude Code sessions:

1. **JSON Schema files** for all 14 entry types in `data/schema/`
   - One .json schema per entry type
   - CI validate.yml currently does manual Python checks — replace with ajv

2. **SHACL shapes** for RDF/JSON-LD validation
   - `data/shacl/mach-shapes.ttl`
   - Use pyshacl in CI

3. **MLDCAT-AP export generator** (`scripts/export_mldcat_ap.py`)
   - Reads entries/models/*.jsonld
   - Outputs /mldcat-ap.jsonld (full export) + per-entry files

4. **CodeMeta export generator** (`scripts/export_codemeta.py`)
   - Reads entries/software/*.jsonld
   - Outputs /codemeta/<slug>.json per entry

5. **landscape2 adapter** (`scripts/generate_landscape2.py`)
   - Reads all entries/*.jsonld
   - Outputs landscape.yml + settings.yml for landscape2
   - landscape2 build → /dist/ → deploy to GitHub Pages

6. **Python FDP server** (new repo: github.com/FORSE-H/mach-fdp)
   - FastAPI + RDFLib + Pydantic
   - Implements specs.fairdatapoint.org
   - Serves MACH catalog entries as DCAT RDF
   - Deploy to Railway or Render (free tier)
   - Stack: FastAPI, RDFLib, Pydantic v2, Postgres (Supabase free tier)

7. **Staleness detection** (`scripts/check_staleness.py`)
   - GitHub Actions scheduled weekly
   - Checks last-commit date on all codeRepository URLs
   - Opens GitHub issue for entries with no release > 18 months

8. **llms.txt generator** (`scripts/generate_llms_txt.py`)
   - Outputs /llms.txt summarising the catalog for LLM ingestion

---

## Grant Information

**open-source funding**
- Application code: 
- Submitted: May 11, 2026
- Deadline was: June 1, 2026 noon CEST
- Amount requested: €50,000
- Rate: €150/hr
- Expected decision: late July / August 2026
- Key deliverables committed: validated schema + CI pipeline +
  MLDCAT-AP/CodeMeta/Croissant exports + 50 curated entries +
  editorial governance system + community launch

---

## Community & Ecosystem

Key relationships (warm, not cold outreach):
- **vantage6 / IKNL** — vantage6 is a seed entry, IKNL is original home
- **DKFZ MIC** — 5 entries from their org (nnU-Net, MITK, Kaapana etc.)
- **YellowBrink** — Dutch openEHR/FHIR community, Priyanka is a member
- **HDRUK** — Health Data Research UK, complementary to MACH
- **FastOMOP / King's College London** — OMCP entry, NHS affiliation
- **openEHR Foundation** — openEHR is a seed entry

Avoid: Health-RI (history of rejection, not collaborative in practice)

Key conferences/venues to announce at:
- FHIR DevDays (Amsterdam, yearly)
- OHDSI Europe Symposium
- YellowBrink webinars
- HDRUK events

---

## Sustainability Plan

Short term (2026): open-source funder grant funds build
Medium term (2027): Apply to Sovereign Tech Fund (need 20+ dependents first)
Long term: Fiscal sponsorship via LF Public Health or LF AI & Data

Possible commercial layer (keeps catalog free):
- Validation-as-a-service API
- Managed hosted FDP instances for hospitals/ministries
- Consulting on MLDCAT-AP compliance

---

## Common Tasks & Commands

```bash
# Add a new entry
cp entries/software/_template.jsonld entries/software/new-project.jsonld
# edit the file, then:
git add entries/software/new-project.jsonld
git commit -m "feat: add [project name]"
git push origin main
# CI runs automatically: validates + updates index.html

# Run validation locally
python scripts/generate_entries.py

# Check for JSON syntax errors across all entries
find entries/ -name "*.jsonld" ! -name "_template.jsonld" | \
  xargs -I{} python3 -c "import json; json.load(open('{}'))" 

# Count total entries
find entries/ -name "*.jsonld" ! -name "_template.jsonld" | wc -l
```

---

## Known Issues & TODO

- [ ] em-dash rendering issue in index.html hero section (CSS ::before)
- [ ] `{entries` ghost folder was created on Windows — should be deleted
- [ ] logos/ folder is empty — need SVG logos for each entry
- [ ] `kubernetes` deployment context not yet in taxonomy/categories.yaml
- [ ] `federated-learning` subcategory not yet in taxonomy/categories.yaml
- [ ] `omop-mcp` subcategory not yet in taxonomy/categories.yaml
- [ ] `experimental` maturity level not yet in taxonomy/categories.yaml
- [ ] JSON Schema files not yet created (data/schema/ is empty)
- [ ] SHACL shapes not yet created
- [ ] No export generators yet (MLDCAT-AP, CodeMeta, Croissant, llms.txt)
- [ ] landscape2 integration not started
- [ ] Python FDP server not started
- [ ] Custom domain not registered yet

---

## Do NOT do these things

- Do NOT create a database before the Python FDP server is designed
- Do NOT force push to main (`git push --force`)
- Do NOT add proprietary/closed-source tools as entries
- Do NOT add entries without a live public codeRepository or URL
- Do NOT skip the mach:judgementReason field — it is what makes MACH
  different from a plain list
- Do NOT use Health-RI as a collaboration partner (see community notes)
- Do NOT hallucinate metadata — verify every field against the actual
  project URL before writing an entry
