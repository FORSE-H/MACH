# MACH — Machine-Actionable Catalog for Healthcare

[![License: Apache-2.0](https://img.shields.io/badge/Code-Apache_2.0-blue.svg)](LICENSE)
[![Data License: CC0-1.0](https://img.shields.io/badge/Data-CC0_1.0-lightgrey.svg)](LICENSE-DATA)
[![Validate](https://github.com/FORSE-H/MACH/actions/workflows/validate.yml/badge.svg)](https://github.com/FORSE-H/MACH/actions/workflows/validate.yml)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.20155320.svg)](https://doi.org/10.5281/zenodo.20155320)
[![SWH](https://archive.softwareheritage.org/badge/origin/https://github.com/FORSE-H/MACH/)](https://archive.softwareheritage.org/browse/origin/?origin_url=https://github.com/FORSE-H/MACH)
[![OpenAIRE](https://img.shields.io/badge/OpenAIRE-indexed-blue)](https://explore.openaire.eu/search/result?pid=10.5281/zenodo.20155320)

An open, machine-actionable catalog of open-source healthcare software, AI/ML models, AI tooling, clinical standards, datasets, and data sources — curated for humans, queryable by agents.

Every entry is a structured JSON-LD record. What makes MACH different from a list is its **judgement**: tools with a public repository get a deterministic **Adopt / Assess / Caution** verdict, derived by a transparent rule-based scorer from measured signals (maintenance, adoption, licence quality) — not hand-written opinion, and never a black box.

**Live catalog:** [machcatalog.org](https://machcatalog.org) · **Status:** Active — 217 entries, CI pipeline live · A project of [FORSE-H](https://github.com/FORSE-H).

---

## Why MACH?

The open healthcare technology ecosystem is fragmented across hundreds of repositories, blog posts, and model cards — none of which is structured for agent discovery or carries a trustworthy judgement of what to adopt.

MACH fills that gap:

- **Judgement, not just listing** — every repo-backed entry carries a deterministic Adopt / Assess / Caution verdict from a rule-based scorer; entries without a harvestable repository signal (datasets, standards, hosted services) show *not scored* rather than a fake verdict.
- **Auditable by design** — each entry's detail page shows every harvested signal and the exact source it came from, plus the rules that produced its judgement. No hallucinated recommendations.
- **Seven entry types** — software, AI/ML models, **AI tooling** (MCP servers, AI agents, agent-skill libraries), datasets, clinical standards, data sources, and catalogs.
- **Verified metadata** — licences are verified against the actual LICENSE file, not just a badge; every entry has at least one live evidence URL.
- **Agent-queryable** — the catalog is served by a live MCP server, so an AI agent can list, search, retrieve, and get the full provenance of any entry.
- **FAIR-aligned** — stable entry URIs, DOI-archived on Zenodo, ORCID-attributed, Software Heritage SWHIDs.

---

## Why open source in healthcare?

Open source enables transparency, reuse, and collaborative improvement. These principles matter everywhere, but are especially critical in healthcare, where the cost of opacity is borne by patients and health systems, not vendors.

- **UK Government (DSIT/GDS, 2026)** · [AI, open code and vulnerability risk in the public sector](https://www.gov.uk/guidance/ai-open-code-and-vulnerability-risk-in-the-public-sector): Recommends "open by default" even in an AI-accelerated threat landscape. Closing source does not remove vulnerabilities — it removes the external scrutiny that helps find and fix them.

- **Ibrahim Haddad, LF AI & Data Foundation (2026)** · [Governing Our Digital Future: Every Government Needs an Open Source Program Office](https://www.linkedin.com/feed/update/urn:li:activity:7463264854640971777/): Open source redistributes cost from vendor licensing to internal capability. Without deliberate governance, those costs accumulate as security and operational risk.

---

## Who is MACH for?

| Audience | Use case |
|---|---|
| **Hospitals & health systems** | Evaluate open-source tools against a consistent, evidence-backed judgement before procurement |
| **Researchers & data scientists** | Discover datasets, models, and pipelines with citable, provenance-rich metadata |
| **AI / agent developers** | Query the catalog programmatically via JSON-LD or the MCP server |
| **Governments & ministries** | Identify open, standards-aligned tooling for national digital health infrastructure |

---

## Catalog categories

| Category | What it covers |
|---|---|
| **Software** | EHR/EMR, imaging tools, pipeline software, clinical systems |
| **AI / ML Models** | Clinical LLMs, imaging foundation models, biomedical NLP |
| **AI Tooling** | MCP servers, AI agents, and agent-skill libraries for healthcare |
| **Datasets** | Benchmarks, clinical datasets, evaluation suites |
| **Data Sources** | Public-health APIs, open data portals, surveillance feeds |
| **Specs** | Interoperability standards and specifications (FHIR, DICOM, openEHR, …) |
| **Catalogs** | Other open healthcare catalogs and registries |

---

## How to use the catalog

**Browse the website:**
Visit **[machcatalog.org](https://machcatalog.org)** for a searchable, filterable view. Each card shows its judgement and GitHub stars; open an entry's **details** page for the full signals-and-lineage table and raw JSON-LD.

**Use the data programmatically:**
All entries are JSON-LD files under `entries/`. Clone the repo or fetch individual entries directly:

```bash
# Clone
git clone https://github.com/FORSE-H/MACH

# Fetch a single entry
curl https://raw.githubusercontent.com/FORSE-H/MACH/main/entries/software/openmrs.jsonld
```

**Entry structure:**
Each entry is a JSON-LD file with a `@context` mapping to schema.org and a small `mach:` vocabulary. Entries carry the stable, human-curated facts; the **judgement and repository signals are not stored in the file** — they are harvested and scored, and live in `data/signals.json`.

```json
{
  "@context": "../../data/context/mach.jsonld",
  "@id": "https://github.com/FORSE-H/MACH/tree/main/entries/software/openmrs",
  "identifier": "openmrs",
  "name": "OpenMRS",
  "description": "...",
  "url": "https://openmrs.org",
  "codeRepository": "https://github.com/openmrs/openmrs-core",
  "license": "MPL-2.0",
  "mach:category": "software",
  "mach:clinicalDomain": ["primary-care", "global-health"],
  "mach:evidence": [{ "@type": "schema:WebPage", "url": "...", "mach:evidenceType": "primary-repo" }],
  "mach:editorialReviewedAt": "2026-05-01"
}
```

> **Note on judgement:** `mach:judgement` is **not** authored in entry files. The Adopt / Assess / Caution verdict is assigned by the scorer from harvested signals and lives in `data/signals.json`. Do not add it (or `mach:maturity`, `mach:licenseVerified`) by hand — see [CONTRIBUTING.md](CONTRIBUTING.md).

**Vocabulary reference:** [`data/context/mach.jsonld`](data/context/mach.jsonld)
**Taxonomy reference:** [`data/taxonomy/categories.yaml`](data/taxonomy/categories.yaml)

---

## How it works

```
GitHub Issue (suggest an entry)  ──►  Maintainer adds a 5-field seed
                                          │
                                          ▼
                         Harvester (ingest.py) fetches signals
                         from GitHub / PyPI / HuggingFace
                                          │
                     ┌────────────────────┼─────────────────────┐
                     ▼                    ▼                      ▼
             repo signals          rule-based scorer       per-field lineage
        (stars, forks, licence,   (Adopt/Assess/Caution,   (source + change
         languages, health)        with the rules shown)     history)
                                          │
                                          ▼
                                   data/signals.json
                     ┌────────────────────┼─────────────────────┐
                     ▼                    ▼                      ▼
            machcatalog.org        /entry/<id> pages        MCP server
         (cards + judgement       (signals & lineage     (list · get · search ·
          + stars + filters)        + raw JSON-LD)         history · explain)
```

The static site is generated from `entries/` + `data/signals.json` and published to GitHub Pages. The harvester runs in the public [`mach-render-deploy`](https://github.com/FORSE-H/mach-render-deploy) repo, which also serves the live REST + MCP API.

---

## Contributing

**Suggest an entry** via a [GitHub Issue](https://github.com/FORSE-H/MACH/issues/new/choose) — give a name and a source URL. A curator adds it as a seed; the harvester fetches the facts and the scorer assigns the judgement. You do not hand-write judgements or metadata.

**Prerequisites for contributors:**
- A GitHub account
- Familiarity with JSON (entries are JSON-LD files)
- A live public source URL for the tool

See [CONTRIBUTING.md](CONTRIBUTING.md) for the entry checklist and conflict-of-interest policy.

---

## License

| What | Licence |
|---|---|
| Code (CI pipeline, scripts, site tooling) | [Apache-2.0](LICENSE) |
| Catalog data (`entries/` JSON-LD files) | [CC0-1.0](LICENSE-DATA) — no rights reserved |

---

## Cite this catalog

```bibtex
@misc{mach2026,
  title   = {MACH: Machine-Actionable Catalog for Healthcare},
  author  = {Ojha, Priyanka},
  year    = {2026},
  doi     = {10.5281/zenodo.20155320},
  url     = {https://zenodo.org/records/20155320},
  orcid   = {https://orcid.org/0000-0002-6844-6493},
  note    = {CC0-1.0}
}
```

---

## Contact & community

- **Issues / suggestions:** [GitHub Issues](https://github.com/FORSE-H/MACH/issues)
- **Discussions:** [GitHub Discussions](https://github.com/FORSE-H/MACH/discussions)
- **Maintainer:** Priyanka Ojha · [ORCID 0000-0002-6844-6493](https://orcid.org/0000-0002-6844-6493)

---

## Roadmap

- Richer repo-health signals on entries (programming languages, tests/CI presence, maintenance)
- Linking tools to the standards they implement (e.g. pydicom → DICOM, HAPI FHIR → FHIR R4)
- Machine-readable exports (CodeMeta, DCAT-AP, Croissant) and `llms.txt`
- Structured, filtered agent queries over the MCP server (by judgement, standard, deployment)
- MCP usage documentation and a stable, documented API

---

## Acknowledgements & references

**Design inspiration**
- [CNCF Landscape](https://landscape.cncf.io/) — category-based open-ecosystem catalog design

**Metadata & interoperability standards** *(the `@context` maps to these vocabularies; standalone exports are on the roadmap)*
- [CodeMeta 3.0](https://codemeta.github.io/) — software metadata crosswalk (schema.org + W3C)
- [MLDCAT-AP 3.0](https://semiceu.github.io/MLDCAT-AP/releases/3.0.0/) (SEMIC / EU) — ML model metadata
- [DCAT-AP 3.0](https://semiceu.github.io/DCAT-AP/releases/3.0.0/) (SEMIC / EU) — dataset and catalog metadata
- [JSON-LD 1.1](https://www.w3.org/TR/json-ld11/) / [schema.org](https://schema.org) (W3C) — linked-data serialisation
- [Model Context Protocol](https://modelcontextprotocol.io/) — the agent interface MACH exposes

**FAIR scoring**
- [FAIRsoft indicators](https://doi.org/10.1093/bioinformatics/btae464) — Martin del Pico et al., 2024
- [FAIR4RS principles](https://doi.org/10.15497/RDA00068) — Chue Hong et al., RDA/FORCE11/ReSA, 2022

**Archival & indexing**
- [Software Heritage](https://www.softwareheritage.org/) — persistent SWHIDs (ISO/IEC 18670)

**License integrity**
- Jewitt et al. (KDD 2026) — [Permissive-Washing in the Open AI Supply Chain: A Large-Scale Audit of License Integrity](https://arxiv.org/abs/2602.08816) — informed MACH's decision to verify actual LICENSE files, not just metadata tags, and to detect licences from file text when a repository's metadata is wrong.

**AI assistance**
- Parts of this project were developed with assistance from [Claude](https://claude.ai) (Anthropic). All content has been reviewed and is the intellectual responsibility of the project curator.
