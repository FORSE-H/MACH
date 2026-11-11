# Adding a resource to MACH

MACH has **two kinds of entry**, added two different ways. Pick the path that
matches the resource before you start.

| If the resource is… | Add it as… | Where |
|---|---|---|
| **Software or an ML model with a public GitHub repo** (stars, releases, a package) | a **seed** → harvested + scored automatically | `mach-backend` (`data/seeds.csv`) |
| **An MCP server, spec, standard, dataset, data-source, or catalog** (institutional, not GitHub-harvestable, needs curator judgement) | a **hand-written JSON-LD entry** | public `MACH` repo (`entries/<category>/`) |

If in doubt: does it have a GitHub repo whose stars / commit activity / downloads
*are* the signal you'd judge it on? → **seed path.** Is it a hosted service, a
standard, or something whose value isn't a repo? → **JSON-LD path.**

---

## Path A — Software / model with a GitHub repo (the harvester path)

The resource becomes a one-line *seed*; the harvester fetches everything else
(description, stars, licence, downloads, last commit) and the scorer assigns the
Adopt / Assess / Caution judgement. You never hand-write metadata.

**One command** (from `mach-backend`):

```bash
# needs a GitHub token (lifts the API rate limit); classic PAT, no scopes needed
export GITHUB_TOKEN=ghp_xxxxx

uv run python scripts/add_resource.py \
  --id my-tool --name "My Tool" \
  --url https://mytool.org \
  --repo https://github.com/org/my-tool \
  --category software \
  --push
```

What it does:

1. appends the seed to `data/seeds.csv` (rejects duplicates / bad categories)
2. rebuilds `data/mach.duckdb` — harvest + score + embed **all** seeds
3. copies the DB into the `mach-render-deploy` repo
4. commits & pushes it (`--push`)

**Final step (manual):** in Render → the `mach-render-deploy` service → click
**Manual Deploy → Deploy latest commit**. (Auto-deploy is off while the deploy
repo is private.) In a minute or two the new entry is live in the API, search,
and MCP tools.

Variations:
- Already edited `seeds.csv` by hand? Just run the script with no `--id` args.
- Rebuild only, don't touch the deploy repo? Add `--no-ship`.
- Build but inspect before pushing? Omit `--push` (it copies the DB but won't push).

`--category` is one of: `software`, `ai-ml-models`, `datasets`, `data-sources`,
`specs`, `mcp-servers`, `catalogs`.

---

## Path B — MCP server / spec / dataset / data-source / catalog (the JSON-LD path)

These get a **hand-written, curator-judged** JSON-LD entry in this repo, because
their value isn't a GitHub repo and they need a real `mach:judgementReason`.

1. Copy an existing entry in the right `entries/<category>/` folder as a template
   (e.g. `entries/mcp-servers/snomed-ct-mcp.jsonld`).
2. Fill in the required fields: `identifier`, `name`, `description`, `url`,
   `license` (SPDX), `mach:category`, `mach:judgement`, `mach:judgementReason`,
   `mach:editorialReviewedAt`, `mach:evidence` (≥1 live URL).
   - **MCP servers** also need `mach:transport` and `mach:authMethod`.
   - **ML models** also need `mach:weightsLicense`, `mach:trainingDataSummary`,
     `mach:intendedUse`.
3. **Verify every field against the real project** — never trust a form
   submission or guess metadata. Check the actual repo for the licence.
4. Validate:
   ```bash
   python scripts/validate_jsonld.py entries/<category>/<id>.jsonld
   python scripts/check_urls.py entries/<category>/<id>.jsonld
   ```
5. Open a PR on a feature branch (`feat/add-<id>`); merge after review.

### Judgement guidance

- **Caution** when the resource is technically open-source but non-functional
  without a proprietary/paid service, or is archived, or has no clear licence.
  (Example: an MIT-licensed MCP client that only works against a vendor's hosted
  paid API — the *code* is open, the *capability* is closed.)
- **Assess** for promising but unproven / early / single-vendor tools.
- **Adopt** for mature, widely-adopted, cleanly-licensed tools.

The `mach:judgementReason` must say *why*, honestly — including the consumer
traps (licence splits, hosted-API dependencies, staleness). That reason is what
makes MACH more than a list.

---

## Rules (both paths)

- No proprietary / closed-source tools as standalone entries. An open-source
  *client* to a closed service can be catalogued, judged **Caution**, with the
  dependency disclosed.
- No entry without a live public code repository or URL.
- Verify every field against the actual project.
- Don't add individual component datasets when a consolidated resource exists.
