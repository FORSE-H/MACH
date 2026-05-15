# Contributing to MACH

Thank you for helping build the Machine-Actionable Catalog for Healthcare.
All catalog data lives as JSON-LD files in `entries/`. Contributions are made via pull request.

---

## Quick start

```bash
git clone https://github.com/FORSE-H/MACH
cd MACH

# Copy the right template for your entry type
cp entries/software/_template.jsonld   entries/software/my-project.jsonld
cp entries/models/_template.jsonld     entries/models/my-model.jsonld
cp entries/standards/_template.jsonld  entries/standards/my-standard.jsonld
cp entries/mcp-servers/_template.jsonld entries/mcp-servers/my-server.jsonld

# Edit the file, then open a PR
```

---

## Entry checklist

Every PR that adds or updates an entry must satisfy the following. CI will check
the schema automatically; the human reviewer checks the rest.

### Required for all entries
- [ ] `identifier` is lowercase, hyphen-separated, globally unique in this repo
- [ ] `name` and `description` are present and accurate
- [ ] `url` and `codeRepository` (if applicable) are live links
- [ ] `license` is a valid SPDX expression (e.g. `Apache-2.0`, `MIT`, `MPL-2.0`)
- [ ] `mach:category` matches one of the 14 categories in `data/taxonomy/categories.yaml`
- [ ] `mach:judgement` is set to one of: `Adopt`, `Situational`, `Assess`, `Caution`
- [ ] `mach:judgementReason` explains *why* in 1–3 sentences
- [ ] At least one `mach:evidence` item points to a primary source (repo, release page, or paper)
- [ ] Logo file is present in `logos/` as an SVG (or PNG if SVG unavailable), max 100 KB

### Additional for software entries (CodeMeta)
- [ ] `softwareVersion` reflects latest stable release
- [ ] `programmingLanguage` is filled in
- [ ] `operatingSystem` or deployment context noted

### Additional for ML model entries (MLDCAT-AP)
- [ ] `mach:weightsLicense` is filled in (may differ from code license)
- [ ] `mach:trainingDataSummary` gives at least one sentence
- [ ] `mach:intendedUse` is filled in
- [ ] `mach:evaluationReference` links to a benchmark or paper if available

### Additional for MCP server entries
- [ ] `mach:transport` is set (`stdio`, `http`, or `sse`)
- [ ] `mach:authMethod` is set (`none`, `oauth2`, `api-key`, or `other`)
- [ ] `mach:fhirVersion` is set if FHIR-related

---

## Judgement criteria

| Level | Use when |
|---|---|
| **Adopt** | Production-ready; actively maintained; used at scale; well-documented; governance is independent or foundation-backed |
| **Situational** | Works well in specific contexts but not a general default; requires deliberate choice |
| **Assess** | Promising; active development; not yet production-proven at scale; worth tracking |
| **Caution** | Unmaintained (>18 months no release); superseded by a better option; significant known issues |

You must provide a `mach:judgementReason` for any level. "Because it is popular" is not sufficient.

---

## Conflict of interest

If you are employed by, or otherwise affiliated with, the organisation behind an entry you are
submitting or amending, you must disclose this in your PR description. Editors will still
accept well-evidenced entries regardless of affiliation, but disclosure is mandatory.

---

## What we do NOT accept

- Proprietary / closed-source products (source code must be publicly available)
- Entries without any public evidence (no repo, no documentation, no paper)
- Entries for projects that are clearly abandoned with no community activity
- Duplicate entries for the same project under different names

---

## Evaluating judgements

Before settling on a judgement level, run the scoring helper against the entry you are adding:

```bash
# Score a single entry (shows editorial + FAIR breakdown)
python scripts/suggest_judgement.py --show-scores --no-fetch

# Include GitHub/PyPI signals (requires GITHUB_TOKEN for > 60 req/hr)
GITHUB_TOKEN=<token> python scripts/suggest_judgement.py --show-scores
```

The script prints suggested vs current judgement with a full signal breakdown
(maturity, governance, forks, PyPI downloads, license, evidence quality).
It does not override editorial discretion — it surfaces signals you might have missed.

---

## Review process

1. CI validates JSON-LD schema and checks for dead links.
2. A human editor reviews the entry checklist above.
3. If the judgement is disputed, the editor will add a comment explaining the concern.
4. Merged entries appear in the next catalog build.

Questions? Open a [GitHub Discussion](https://github.com/FORSE-H/MACH/discussions) or
email the maintainer (see the README).
