# Entry Writing Guide

How to research and write a MACH entry correctly.
**Golden rule: verify every field against the actual URL. No guessing.**

---

## Research checklist before writing

For every new entry, open these in your browser and verify:

- [ ] Primary URL is live
- [ ] GitHub/GitLab repo is public and exists
- [ ] License is confirmed (check LICENSE file in repo, not just README)
- [ ] Latest release/version confirmed (check GitHub releases tab)
- [ ] Last commit date confirmed (check repo insights or commit history)
- [ ] Description is accurate (read the actual README, not marketing copy)
- [ ] For models: weights license, training data, intended use confirmed

---

## Judgement criteria (be honest, be specific)

**Adopt** — ALL of these should be true:
- Actively maintained (release in last 12 months)
- Production deployments documented
- Clear governance (foundation, established academic group, or very active community)
- Well-documented
- Multiple independent users/deployments

**Situational** — right for specific use cases, not a general default:
- Works well but only in specific contexts (e.g. only for Netherlands, only for oncology)
- Or: technically good but requires unusual infrastructure
- Or: important but overlaps with a stronger Adopt option

**Assess** — promising but not yet proven:
- Active development
- Peer-reviewed paper or credible backing
- BUT: pre-1.0, or limited production deployments, or academic governance only
- OR: very new (< 12 months since first release)

**Caution** — avoid for new work:
- No release in 18+ months
- Superseded by a better option (mention the alternative)
- Known significant issues
- Still listed because encountered in existing systems

---

## The judgementReason field

This is what makes MACH credible. Write it well.

**Bad:** "This is a popular tool used by many people."
**Bad:** "Well-maintained open source project."
**Good:** "nnU-Net's self-configuring approach has dominated MICCAI
segmentation challenges since 2018 and is cited in thousands of papers.
Nature Methods 2021 publication, Apache-2.0, pip-installable, 8,000+
GitHub stars. The principal caution is academic governance (single lab)
but the principal author is exceptionally active."

Structure: [What makes it good/notable] + [Evidence] + [Caveats if any]

---

## Evidence types

Use these values for `mach:evidenceType`:

| Value | Use for |
|---|---|
| `primary-repo` | Main GitHub/GitLab repository |
| `documentation` | Official docs site |
| `academic-reference` | Peer-reviewed paper or preprint |
| `package-registry` | PyPI, npm, crates.io, Docker Hub |
| `specification` | Official spec document |
| `deployment-evidence` | A known production deployment |
| `model-hub` | Hugging Face, MONAI Model Zoo |
| `zenodo-doi` | Zenodo archive with DOI |
| `research-software-directory` | research-software.nl or similar |
| `release` | Link to specific release |
| `regulatory-reference` | Government/regulatory mandate |
| `related-resource` | Related but not primary |

---

## Category placement decisions

When a project could fit multiple categories, use this priority:

1. What does the project primarily DO (not what it's built with)?
2. Who is the primary user (clinician, developer, researcher, agent)?
3. Where would someone logically look for it?

Examples:
- PyHealth → `tooling-infrastructure` (it's a development framework)
  NOT `ai-ml-models` (it doesn't ship a model, it helps you build one)
- vantage6 → `tooling-infrastructure` (it's a federated learning platform)
  NOT `deidentification-privacy` (privacy is a feature, not the category)
- Kaapana → `tooling-infrastructure` (it's a platform/orchestrator)
  NOT `medical-imaging-signals` (imaging is what it runs, not what it is)
- OMCP → `mcp-servers-ai-interfaces` (it is an MCP server)
  NOT `tooling-infrastructure` or `data-models-research`

---

## Schema:comment field

Use this for notes that should NOT appear in public exports:
- Suggestions for follow-on entries ("also add EHRbase")
- Taxonomy additions needed ("add omop-mcp subcategory")
- Editorial uncertainty ("verify license — README says MIT but no LICENSE file")
- Reminders for re-review ("re-check judgement in 6 months, project is moving fast")

This field is ignored by all export generators.

---

## Common mistakes to avoid

1. **License wrong** — always check the actual LICENSE file, not the README badge
   (badges can be stale, wrong, or aspirational)

2. **Version inflated** — use the latest *stable* release, not a pre-release.
   If there are no releases, use `"softwareVersion": "unreleased"` or omit.

3. **codeRepository != url** — url is the project homepage/website.
   codeRepository is the source code location. They are often different.
   (e.g. url: https://vantage6.ai, codeRepository: https://github.com/vantage6/vantage6)

4. **AGPL confusion** — AGPL-3.0 means if you *deploy a modified version as a service*
   you must release your modifications. This affects hospitals and cloud providers.
   Always flag AGPL explicitly in judgementReason.

5. **Academic governance** — individual/academic governance is NOT a disqualifier for
   Adopt, but always mention it in judgementReason so users know the bus-factor risk.
   nnU-Net, PyHealth, TractSeg are all Adopt despite academic governance.

6. **altName vs name** — use `alternateName` for abbreviations and previous names,
   not for the official full name. The `name` field should match how the project
   refers to itself (usually the GitHub repo name or the homepage H1).
