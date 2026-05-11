# MACH Roadmap

## Phase 1 — Foundation (COMPLETE as of May 2026)

Done without funding, as proof of concept:

- [x] Repo structure, licenses, governance, contributing guide
- [x] JSON-LD context (`data/context/mach.jsonld`)
- [x] 14-category taxonomy (`data/taxonomy/categories.yaml`)
- [x] 13 seed entries across 6 categories
- [x] CI validation pipeline (GitHub Actions)
- [x] CI site generator (auto-updates index.html on push)
- [x] GitHub Pages landing site live
- [x] open-source funding application submitted ()

---

## Phase 2 — open-source funder Build (pending grant approval, ~Aug–Dec 2026)

### Sprint 1: Schema hardening (T1 — 40h)
- [ ] JSON Schema files for all 14 entry types (`data/schema/`)
- [ ] Replace manual Python field checks in validate.yml with ajv
- [ ] SHACL shapes (`data/shacl/mach-shapes.ttl`) + pyshacl in CI
- [ ] Fix known taxonomy gaps:
  - [ ] Add `kubernetes` to deployment_contexts
  - [ ] Add `federated-learning` to tooling-infrastructure subcategories
  - [ ] Add `omop-mcp` to mcp-servers-ai-interfaces subcategories
  - [ ] Add `experimental` to maturity_levels

### Sprint 2: Export generators (T2 + T6 — 85h)
- [ ] MLDCAT-AP 3.0 export (`scripts/export_mldcat_ap.py`)
  - Output: `/mldcat-ap.jsonld` + per-entry `/mldcat-ap/<slug>.jsonld`
- [ ] CodeMeta 3.0 export (`scripts/export_codemeta.py`)
  - Output: `/codemeta/<slug>.json`
- [ ] MLCommons Croissant export (`scripts/export_croissant.py`)
  - Output: `/croissant/<slug>.json` for dataset entries
- [ ] MCP server.json export (`scripts/export_mcp_servers.py`)
  - Output: `/mcp/<slug>.server.json`
- [ ] llms.txt generator (`scripts/generate_llms_txt.py`)
  - Output: `/llms.txt`
- [ ] Full catalog JSON-LD (`scripts/generate_catalog.py`)
  - Output: `/catalog.jsonld`
- [ ] Zenodo release workflow (GitHub Actions on git tag)
- [ ] Stable URI strategy with w3id.org redirects

### Sprint 3: landscape2 integration (T2 — part of CI pipeline)
- [ ] `scripts/generate_landscape2.py` — JSON-LD → landscape2 YAML adapter
- [ ] `settings/landscape2-settings.yml` — categories, colours, logo
- [ ] CI step: landscape2 Docker build → /dist/
- [ ] Deploy /dist/ to GitHub Pages (replace current index.html approach)
- [ ] Verify grid view, radar view, table view, search all work
- [ ] Per-entry detail pages / drawers working

### Sprint 4: Curation — 43 new entries (T3 — 130h)
Target entries to add (in priority order):
1. OpenEMR (clinical-systems/ehr)
2. Bahmni (clinical-systems/ehr)
3. HAPI FHIR Server (tooling-infrastructure)
4. DHIS2 (public-health-epi)
5. MONAI (medical-imaging-signals)
6. Orthanc (medical-imaging-signals/pacs)
7. OHIF Viewer (medical-imaging-signals/dicom-viewer)
8. 3D Slicer (medical-imaging-signals)
9. EHRbase (clinical-systems — openEHR CDR)
10. OMOP CDM (data-models-research)
11. TotalSegmentator (medical-imaging-signals)
12. GNU Health (clinical-systems)
13. scispaCy (ai-ml-models/nlp-ner)
14. MedSAM (medical-imaging-signals/imaging-model)
15. Inferno ONC (quality-conformance)
16. Snowstorm (tooling-infrastructure/terminology-server)
17. SORMAS (public-health-epi)
18. Philter (deidentification-privacy)
19. openEHR CKM (data-models-research)
20. FAIR Data Point (tooling-infrastructure) ← build this THEN add it
21. + 23 more from contacts list

### Sprint 5: Editorial governance system (T4 — 30h)
- [ ] Staleness detection script (`scripts/check_staleness.py`)
  - Scheduled GitHub Action (weekly)
  - Checks last-commit/last-release on all codeRepository URLs via GitHub API
  - Opens GitHub issue for entries where last release > 18 months
- [ ] Promotion workflow: documented criteria for Assess → Adopt
- [ ] Demotion workflow: documented criteria for any → Caution
- [ ] Archival workflow: entries for abandoned projects moved to /archive/
- [ ] COI tooling: PR template enforces disclosure checkbox
- [ ] Appeal process: documented in GOVERNANCE.md with response SLA

### Sprint 6: MCP registry integration (T5 — 20h)
- [ ] Align all MCP server entries with upstream MCP registry server.json spec
- [ ] Healthcare MCP server discovery workflow
- [ ] Submit MACH MCP entries to upstream MCP registry where applicable

### Sprint 7: Python FDP server (T2/T6 — separate repo)
New repo: `github.com/FORSE-H/mach-fdp`
- [ ] FastAPI skeleton implementing FDP spec (specs.fairdatapoint.org)
- [ ] RDFLib DCAT serialisation layer
- [ ] Pydantic models for Catalog, Dataset, Distribution
- [ ] Postgres adapter (Supabase free tier)
- [ ] Sync script: JSON-LD entries → FDP Postgres
- [ ] Full-text search endpoint (pg_trgm)
- [ ] Deploy to Railway/Render free tier
- [ ] Cross-link landscape2 detail pages ↔ FDP entry URIs
- [ ] Release as standalone open-source library (pip installable)

### Sprint 8: Community launch (T7 — 20h)
- [ ] Register custom domain (openmach.health or openmach.org)
- [ ] Announcement post for YellowBrink community
- [ ] OHDSI mailing list announcement
- [ ] FHIR Zulip announcement
- [ ] HDRUK outreach email
- [ ] vantage6 community announcement
- [ ] First Zenodo-archived release with DOI (v1.0)
- [ ] BibTeX citation updated with DOI

---

## Phase 3 — Growth (2027, post-open-source funder)

- [ ] Apply to Sovereign Tech Fund (need 20+ dependents by then)
- [ ] 200+ entries
- [ ] Multiple curators onboarded
- [ ] Fiscal sponsorship (LF Public Health or LF AI & Data)
- [ ] SPARQL endpoint
- [ ] MLDCAT-AP 4.0 migration (if released)
- [ ] EU AI Act Annex IV fields on all AI model entries
- [ ] Consider Vercel + Supabase backend for full search API

---

## Notes for Claude Code sessions

When starting a new Claude Code session on this repo:
1. Read CLAUDE.md first (it is in the repo root)
2. Check the Known Issues section in CLAUDE.md before touching anything
3. Always verify entry metadata against actual project URLs — no hallucinations
4. Run `find entries/ -name "*.jsonld" ! -name "_template.jsonld" | wc -l`
   to check current entry count before claiming a number
5. Always `git pull origin main --rebase` before pushing
