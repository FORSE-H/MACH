# ADR-001: JSON-LD Files as Canonical Source of Truth

**Date:** May 2026
**Status:** Accepted
**Decided by:** Priyanka Ojha (founder)

## Context

MACH needs a data store for catalog entries. Options considered:
- A database (Postgres, SQLite, MongoDB)
- A headless CMS
- YAML files (like landscape2 uses)
- JSON-LD files in Git

## Decision

All catalog entries are stored as individual JSON-LD files in the
`entries/` directory of the Git repository. Git is the database.

## Rationale

- Every change is a commit — full audit trail, no separate audit log needed
- PRs are the contribution mechanism — familiar to open-source contributors
- SHACL and JSON Schema validation run on every PR in CI
- JSON-LD is machine-readable by design — no transformation needed for
  semantic web consumers
- Zero hosting cost — no database server to maintain
- Portable — the entire catalog can be cloned in seconds
- Aligned with how CodeMeta, CITATION.cff, and ODPS work

## Consequences

- No real-time querying at MVP — full-text search requires either
  client-side (landscape2) or a separate index (Phase 2 FDP server)
- Contributors need basic Git knowledge to submit entries
- CI must validate entries on every PR to maintain quality

## Review trigger

Revisit if entries exceed 2,000 and Git performance degrades.
