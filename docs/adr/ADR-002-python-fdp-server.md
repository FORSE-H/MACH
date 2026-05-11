# ADR-002: Build a Python FDP Server Rather Than Use Existing Implementations

**Date:** May 2026
**Status:** Accepted — planned for Phase 2
**Decided by:** Priyanka Ojha

## Context

MACH needs a searchable, FAIR-compliant catalog interface similar to
fdp.radboudumc.nl. The FAIR Data Point (FDP) spec at specs.fairdatapoint.org
is the right standard — it is DCAT-based, REST, semantic web aligned.

Existing implementations evaluated:

| Implementation | Language | Status | Verdict |
|---|---|---|---|
| FAIRDataTeam/FAIRDataPoint | Java/Spring | Active but buggy | Rejected — heavy, buggy, Java |
| NLeSC/fairdatapoint | Python | ~5 years unmaintained | Rejected — too old |
| MOLGENIS FDP | Java | Domain-specific | Rejected — not reusable |
| Castor | Proprietary | Old version only | Rejected |

## Decision

Build a new lightweight Python FDP server as a separate open-source
project (`github.com/FORSE-H/mach-fdp`) that implements the FDP spec
and serves MACH's JSON-LD catalog entries.

## Stack

- **FastAPI** — REST API, async, auto-docs via OpenAPI
- **RDFLib** — RDF/Turtle/JSON-LD serialisation for DCAT compliance
- **Pydantic v2** — data validation of DCAT/MLDCAT models
- **PostgreSQL** — entry storage + full-text search (pg_trgm or pgvector)
- **Supabase or Neon** — managed Postgres, free tier sufficient for MVP
- **Railway or Render** — hosting, free tier, auto-deploy from GitHub

## Rationale

- Python is the dominant language in the healthcare AI/data science community
- FastAPI is lightweight, well-documented, and familiar
- A clean implementation of the FDP spec has value beyond MACH —
  other healthcare catalogs can reuse it
- Postgres gives us full-text search without a separate search index
- This is within scope of the open-source funder grant (T2 + T6 in the budget)

## Consequences

- Additional open-source project to maintain
- Phase 2 work — not started until open-source funder funding confirmed
- The JSON-LD entries remain the source of truth; the FDP server
  reads from them via an adapter/sync script

## Note on Health-RI

Priyanka Ojha has previously contributed bug fixes to Health-RI's
FDP implementation and received no credit or engagement. Do NOT
frame this project as dependent on or derivative of Health-RI.
This is an independent implementation of an open specification.
