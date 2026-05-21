# MACH — Machine-Actionable Catalog for Healthcare

[![License: Apache-2.0](https://img.shields.io/badge/Code-Apache_2.0-blue.svg)](LICENSE)
[![Data License: CC-BY-4.0](https://img.shields.io/badge/Data-CC--BY--4.0-lightgrey.svg)](LICENSE-DATA)
[![Validate](https://github.com/FORSE-H/MACH/actions/workflows/validate.yml/badge.svg)](https://github.com/FORSE-H/MACH/actions/workflows/validate.yml)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.20155320.svg)](https://doi.org/10.5281/zenodo.20155320)
[![SWH](https://archive.softwareheritage.org/badge/origin/https://github.com/FORSE-H/MACH/)](https://archive.softwareheritage.org/browse/origin/?origin_url=https://github.com/FORSE-H/MACH)
[![OpenAIRE](https://img.shields.io/badge/OpenAIRE-indexed-blue)](https://explore.openaire.eu/search/result?pid=10.5281/zenodo.20155320)

An open, machine-actionable catalog of open-source healthcare software, AI/ML models, clinical standards, datasets, and MCP servers — curated for humans, queryable by agents.

Every entry is a structured JSON-LD record aligned with established open metadata standards (CodeMeta, MLDCAT-AP, DCAT-AP, Croissant), so hospitals, researchers, governments, and AI agents can discover and consume the open healthcare commons.

**Project status:** Active — CI pipeline live. A project of [FORSE-H](https://github.com/FORSE-H).

---

## Why MACH?

The open healthcare technology ecosystem is fragmented across hundreds of repositories, blog posts, and HuggingFace model cards — none of which is structured for agent discovery or aligned with open metadata standards.

MACH fills that gap:

- **Structured, evidence-backed entries** — every entry includes a curated rationale, clinical domain tags, deployment context, and at least one live evidence URL
- **Three-ring editorial judgement** — Adopt / Assess / Caution, data-driven and explained, adapted from the [ThoughtWorks Technology Radar](https://www.thoughtworks.com/radar)
- **Machine-readable exports** — MLDCAT-AP 3.0, CodeMeta 3.0, DCAT-AP, Croissant, llms.txt
- **FAIR alignment** — stable entry URIs, DOI-archived on Zenodo, ORCID-attributed
- **Agent-native** — MCP server and FAIR Data Point RDF/SPARQL endpoint (Phase 2)

---

## Who is MACH for?

| Audience | Use case |
|---|---|
| **Hospitals & health systems** | Evaluate open-source tools against structured criteria before procurement |
| **Researchers & data scientists** | Discover FAIR-aligned datasets, models, and pipelines with citable metadata |
| **AI / agent developers** | Query the catalog programmatically via JSON-LD, MCP server, or SPARQL |
| **Governments & ministries** | Identify open standards-compliant tooling for national digital health infrastructure |

---

## Catalog categories

| Category | What it covers |
|---|---|
| **Software** | EHR/EMR, imaging tools, pipeline software, clinical systems |
| **AI / ML Models** | Clinical LLMs, imaging foundation models, NLP |
| **Datasets** | Benchmarks, clinical datasets, evaluation suites |
| **MCP Servers** | FHIR MCP, OMOP MCP, clinical AI interfaces |
| **Data Sources** | Public health APIs, open data portals, surveillance feeds |
| **Catalogs** | Other open healthcare catalogs and registries |
| **Specs** | Interoperability standards and specifications |

---

## How to use the catalog

**Browse the website:**
Visit the [GitHub Pages site](https://forse-h.github.io/MACH) for a searchable, filterable view of all entries.

**Use the data programmatically:**
All entries are JSON-LD files in `entries/`. Clone the repo or fetch individual entries directly:

```bash
# Clone
git clone https://github.com/FORSE-H/MACH

# Fetch a single entry
curl https://raw.githubusercontent.com/FORSE-H/MACH/main/entries/software/openmrs.jsonld
```

**Entry structure:**
Each entry is a JSON-LD file with fields from CodeMeta, MLDCAT-AP, and the MACH vocabulary:

```json
{
  "@context": "../../data/context/mach.jsonld",
  "identifier": "openmrs",
  "name": "OpenMRS",
  "description": "...",
  "url": "https://openmrs.org",
  "license": "MPL-2.0",
  "mach:judgement": "Adopt",
  "mach:judgementReason": "...",
  "mach:clinicalDomain": ["primary-care", "global-health"],
  "mach:evidence": [...]
}
```

**Vocabulary reference:** [`data/context/mach.jsonld`](data/context/mach.jsonld)
**Taxonomy reference:** [`data/taxonomy/categories.yaml`](data/taxonomy/categories.yaml)

---

## How it works

```
GitHub Issue (suggest an entry)
         │
         ▼ Maintainer approves → CI harvests from source systems
         │
         ▼
      DuckDB  ←  GitHub API · PyPI · OpenAlex · arXiv
         │
         ├── Scoring (Adopt / Assess / Caution)
         ├── Validation
         └── Draft PR → Maintainer reviews → Merges
                  │
                  ▼
         Catalog goes live
         ├── GitHub Pages (searchable UI)
         ├── JSON-LD entries (this repo)
         ├── FDP / SPARQL endpoint (Phase 2)
         └── MCP server (Phase 2)
```

---

## Contributing

**Suggest an entry** via a [GitHub Issue](https://github.com/FORSE-H/MACH/issues/new/choose) — fill in the template with a name and source URL. The CI pipeline handles harvesting and metadata enrichment; a curator reviews before anything goes live.

**Prerequisites for contributors:**
- A GitHub account
- Familiarity with JSON (entries are JSON-LD files)
- Access to the project's source URL for the tool you're suggesting

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full entry checklist, judgement criteria, and conflict-of-interest policy.

---

## License

| What | Licence |
|---|---|
| Code (CI pipeline, scripts, site tooling) | [Apache-2.0](LICENSE) |
| Catalog data (`entries/` JSON-LD files) | [CC-BY-4.0](LICENSE-DATA) |

Attribution for data reuse:
> *MACH — Machine-Actionable Catalog for Healthcare, FORSE-H, https://github.com/FORSE-H/MACH*

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
  note    = {CC-BY-4.0}
}
```

---

## Contact & community

- **Issues / suggestions:** [GitHub Issues](https://github.com/FORSE-H/MACH/issues)
- **Discussions:** [GitHub Discussions](https://github.com/FORSE-H/MACH/discussions)
- **Maintainer:** Priyanka Ojha · [ORCID 0000-0002-6844-6493](https://orcid.org/0000-0002-6844-6493)

---

## Acknowledgements

Inspired by [CNCF Landscape](https://landscape.cncf.io/), [ThoughtWorks Tech Radar](https://www.thoughtworks.com/radar), [Research Software Directory](https://research-software-directory.org/) (Netherlands eScience Center), and [bio.tools](https://bio.tools/) (ELIXIR).

Metadata standards: [MLDCAT-AP](https://semiceu.github.io/MLDCAT-AP/releases/3.0.0/) (SEMIC/EU) · [CodeMeta](https://codemeta.github.io/) · [DCAT-AP](https://semiceu.github.io/DCAT-AP/) · [Croissant](https://mlcommons.org/working-groups/data/croissant/) · [FAIR Data Point](https://specs.fairdatapoint.org/) · [ODRL](https://www.w3.org/TR/odrl-model/) (W3C).

FAIR scoring informed by [FAIRsoft](https://doi.org/10.1093/bioinformatics/btae464) (Martin del Pico et al., 2024), [FAIR4RS](https://doi.org/10.15497/RDA00068) (Chue Hong et al., 2022), and [howfairis](https://github.com/fair-software/howfairis) (Netherlands eScience Center).

Persistent archival via [Software Heritage](https://www.softwareheritage.org/) (SWHIDs, ISO/IEC 18670) and [Zenodo](https://zenodo.org).

Parts of this project were developed with assistance from [Claude](https://claude.ai) by [Anthropic](https://www.anthropic.com). All content has been reviewed and is the intellectual responsibility of the project curator.
