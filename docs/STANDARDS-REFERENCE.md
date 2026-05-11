# Standards Reference

Quick reference for every standard used in MACH entries.
Read this before writing or modifying any entry or export script.

---

## MLDCAT-AP 3.0
**What:** EU application profile for ML model metadata, AI Act aligned
**URL:** https://semiceu.github.io/MLDCAT-AP/releases/3.0.0/
**GitHub:** https://github.com/SEMICeu/MLDCAT-AP
**Used for:** All `entries/models/*.jsonld`
**Key fields we use:**
- `mach:weightsLicense` — license for model weights (may differ from code)
- `mach:trainingDataSummary` — plain-text summary of training data
- `mach:intendedUse` — intended use and out-of-scope uses
- `mach:aiActRiskClass` — EU AI Act risk classification
- `mach:evaluationReference` — links to benchmark papers
**Note:** 4.0 expected in 2026 — when released, run migration script

---

## CodeMeta 3.0
**What:** Metadata schema for research software, JSON-LD based
**URL:** https://codemeta.github.io/
**Context URL:** https://w3id.org/codemeta/3.0
**Used for:** All `entries/software/*.jsonld`
**Key fields:**
- `codeRepository`, `contIntegration`, `issueTracker`, `relatedLink`
- `softwareVersion`, `dateModified`, `programmingLanguage`
- `license` (SPDX expression), `copyrightHolder`
**Note:** Most fields already in our template. CodeMeta is also how
  CITATION.cff relates to JSON-LD.

---

## DCAT-AP 3.0
**What:** EU application profile of W3C DCAT for open data catalogs
**URL:** https://semiceu.github.io/DCAT-AP/
**Used for:** The catalog itself + dataset entries
**Key classes:** dcat:Catalog, dcat:Dataset, dcat:Distribution
**Note:** The MACH catalog.jsonld is itself a DCAT Catalog

---

## MLCommons Croissant
**What:** JSON-LD format for ML dataset metadata
**URL:** https://mlcommons.org/working-groups/data/croissant/
**GitHub:** https://github.com/mlcommons/croissant
**Used for:** `entries/datasets/*.jsonld`
**Note:** Hugging Face, Kaggle, and OpenML support Croissant natively

---

## MCP server.json
**What:** Descriptor format for Model Context Protocol servers
**URL:** https://github.com/modelcontextprotocol/registry
**Used for:** `entries/mcp-servers/*.jsonld`
**Our fields:** mach:transport, mach:authMethod, mach:fhirVersion, mach:mcpSpecVersion
**Transport values:** stdio | http | sse
**Auth values:** none | oauth2 | api-key | other

---

## FAIR Data Point Specification
**What:** REST API spec for FAIR-compliant metadata endpoints
**URL:** https://specs.fairdatapoint.org/
**Reference implementation:** github.com/FAIRDataTeam/FAIRDataPoint (Java — buggy)
**Python impl (old):** github.com/NLeSC/fairdatapoint (unmaintained)
**Our plan:** Build fresh Python implementation (github.com/FORSE-H/mach-fdp)
**Based on:** DCAT + Dublin Core + Linked Data Platform (LDP) + REST
**Hierarchy:** FDP → Catalogs → Datasets → Distributions

---

## Bitol ODPS
**What:** Open Data Product Standard — YAML spec for data products
**URL:** https://github.com/bitol-io/open-data-product-standard
**Used for:** When an entry exposes a structured data product
**Note:** Under LF AI & Data Foundation — good alignment for partnerships

---

## SPDX
**What:** Software Package Data Exchange — license identifiers
**URL:** https://spdx.org/licenses/
**Used for:** `license` field in all entries
**Common values:**
- Apache-2.0, MIT, BSD-3-Clause, BSD-2-Clause
- GPL-3.0-only, AGPL-3.0-only (note: AGPL has service-deployment implications)
- MPL-2.0, LGPL-3.0-only
- CC-BY-4.0, CC0-1.0 (for data/standards)
- CC-BY-3.0 (openEHR uses this)

---

## FAIR Principles
**What:** Findable, Accessible, Interoperable, Reusable
**URL:** https://doi.org/10.1038/sdata.2016.18 (original paper)
**Relevance:** MACH's machine-readable exports make catalog entries FAIR
**F** — stable URIs, catalog.jsonld, llms.txt
**A** — public GitHub repo, open licenses, HTTP access
**I** — JSON-LD, DCAT-AP, MLDCAT-AP, CodeMeta
**R** — CC-BY-4.0 data license, provenance in evidence blocks

---

## Vocabulary prefixes used in MACH

```
schema:   https://schema.org/
codemeta: https://w3id.org/codemeta/3.0#
dcat:     http://www.w3.org/ns/dcat#
dcterms:  http://purl.org/dc/terms/
mach:     https://github.com/FORSE-H/MACH/blob/main/data/context/mach.jsonld#
spdx:     https://spdx.org/rdf/terms/#
```
