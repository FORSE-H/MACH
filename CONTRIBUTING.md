# Contributing to MACH

## Suggest an entry

Open a [GitHub Issue](https://github.com/FORSE-H/MACH/issues/new/choose) using the
**Suggest an entry** template. Fill in the name and a source URL. That's it.

The curator reviews every suggestion. Suitable entries are harvested, scored, and added
to the catalog. You will be notified in the issue thread.

### Authoring an entry (maintainers)

Start from the empty template for the entry's category — `entries/<category>/_template.jsonld` —
never by copying a neighbouring real entry. Cloning a real entry is how one entry's
`url` or `relatedLink` ends up pointing at a *different* project. CI enforces this:

- `scripts/check_placeholders.py` fails the build if any `REPLACE-*`, `YYYY-MM-DD`,
  or `SPDX-EXPRESSION-HERE` placeholder is left unfilled.
- `scripts/check_entry_leaks.py` fails the build if an entry's `relatedLink` points at
  another entry's folder.

Set `url` to the entry's **own** page. Leave `mach:subcategory` out — `scripts/classify.py`
assigns it. Do not add `mach:judgement` — the scorer derives it from harvested signals.

---

## What makes a good suggestion

- The project is open-source with a public repository or specification URL
- It is healthcare-specific or healthcare-relevant
- It is actively maintained or is an established standard
- You can link to at least one piece of public evidence (repo, paper, or documentation)

## What we do not accept

- Proprietary or closed-source products
- Projects without any public evidence
- Clearly abandoned projects with no community activity
- Individual component datasets when a consolidated resource already exists in the catalog

---

## Conflict of interest

If you are affiliated with the organisation behind an entry you are suggesting, say so in
the issue. It does not disqualify the suggestion, but disclosure is required.

---

## Questions

Open a [GitHub Discussion](https://github.com/FORSE-H/MACH/discussions) or
email the maintainer (see the README).
