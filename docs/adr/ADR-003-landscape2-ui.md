# ADR-003: Use landscape2 as the Interactive Landscape UI

**Date:** May 2026
**Status:** Accepted — planned for Phase 2
**Decided by:** Priyanka Ojha

## Context

MACH needs an interactive landscape view — grid, radar, table —
similar to landscape.cncf.io. Building this from scratch would
reinvent a proven wheel.

## Decision

Use CNCF landscape2 (github.com/cncf/landscape2) as the rendering
engine for the interactive landscape view.

An adapter script (`scripts/generate_landscape2.py`) converts
MACH's JSON-LD entries into landscape2's YAML format.

## Why landscape2

- Battle-tested — used by 20+ major landscapes
- Free, open source (Apache-2.0), actively maintained by CNCF
- Grid view, radar view, table view out of the box
- Built-in search (client-side, fast, fuzzy)
- Per-entry detail drawers
- Embed support
- Static output — deploys to GitHub Pages, zero hosting cost

## Adapter design

```
entries/**/*.jsonld
    ↓ scripts/generate_landscape2.py
landscape.yml + settings.yml
    ↓ landscape2 build (Rust CLI via Docker)
/dist/ (static site)
    ↓ GitHub Pages deploy
forse-h.github.io/MACH
```

## Consequences

- Rust CLI dependency in CI (use official landscape2 Docker image)
- landscape2 YAML schema must be kept in sync with mach: taxonomy
- landscape2 is the UI layer only — JSON-LD remains source of truth
- If landscape2 is ever abandoned, the adapter can target a different UI

## Relationship to FDP server

landscape2 handles human browsing.
The FDP server handles machine/agent querying.
Both are fed from the same JSON-LD source files.
landscape2 detail pages will link to FDP entry URIs.
