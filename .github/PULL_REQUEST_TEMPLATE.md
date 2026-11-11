## Entry PR Checklist

**Entry type:** <!-- software / model / dataset / data-source / spec / catalog / ai-tooling -->
**Entry slug:** <!-- e.g. openmrs -->
**Action:** <!-- new entry / update existing / remove -->

> **Judgement is rule-based.** MACH's Adopt / Assess / Caution verdict is assigned
> deterministically by the scorer from harvested signals (stars, maintenance,
> licence) — it is **not** written by hand. Do **not** add `mach:judgement` or
> `mach:judgementReason` to entry files; the harvester and `data/signals.json`
> own them. Entries with no harvestable repository signal show "not scored".

---

### All entries
- [ ] JSON parses without errors
- [ ] `identifier` is lowercase, hyphen-separated
- [ ] `name`, `description`, `url` are accurate and live
- [ ] `license` is a valid SPDX expression (or `LicenseRef-no-license-file` if the repo has none)
- [ ] `mach:category` matches a category in `data/taxonomy/categories.yaml`
- [ ] `mach:subcategory` set where it applies (e.g. ai-tooling: `ai-agent` / `agent-skills` / `mcp-server` / `ai-swarm`)
- [ ] At least one `mach:evidence` item with a live URL
- [ ] `mach:editorialReviewedAt` set to today (YYYY-MM-DD)
- [ ] Logo file added to `logos/` (SVG preferred, max 100 KB) — optional

### For ML model entries
- [ ] `mach:weightsLicense` filled in
- [ ] `mach:trainingDataSummary` filled in
- [ ] `mach:intendedUse` filled in
- [ ] `mach:aiActRiskClass` set where clinical/high-risk

### For MCP server entries (category `ai-tooling`, subcategory `mcp-server`)
- [ ] `mach:transport` filled in
- [ ] `mach:authMethod` filled in

> **Do NOT include** `mach:judgement`, `mach:judgementReason`, `mach:maturity`, or
> `mach:licenseVerified` — these are derived by the scorer/harvester, not authored.

---

### Conflict of interest disclosure
<!-- If you are employed by or affiliated with the organisation behind this entry, disclose here. -->
No conflict of interest / I am affiliated with [org] and disclose this here.

---

### Notes for reviewer
<!-- Anything else the reviewer should know -->
