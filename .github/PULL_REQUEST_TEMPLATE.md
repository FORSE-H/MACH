## Entry PR Checklist

**Entry type:** <!-- software / model / standard / mcp-server / dataset -->
**Entry slug:** <!-- e.g. openmrs -->
**Action:** <!-- new entry / update existing / remove -->

---

### All entries
- [ ] JSON parses without errors
- [ ] `identifier` is lowercase, hyphen-separated
- [ ] `name`, `description`, `url` are accurate and live
- [ ] `license` is a valid SPDX expression
- [ ] `mach:category` matches a category in `data/taxonomy/categories.yaml`
- [ ] `mach:judgement` is one of: `Adopt` / `Assess` / `Caution`
- [ ] `mach:judgementReason` explains the judgement in 1–3 sentences
- [ ] At least one `mach:evidence` item with a live URL
- [ ] Logo file added to `logos/` (SVG preferred, max 100 KB)

### For ML model entries
- [ ] `mach:weightsLicense` filled in
- [ ] `mach:trainingDataSummary` filled in
- [ ] `mach:intendedUse` filled in

### For MCP server entries
- [ ] `mach:transport` filled in
- [ ] `mach:authMethod` filled in

---

### Conflict of interest disclosure
<!-- If you are employed by or affiliated with the organisation behind this entry, disclose here. -->
No conflict of interest / I am affiliated with [org] and disclose this here.

---

### Notes for reviewer
<!-- Anything else the reviewer should know -->
