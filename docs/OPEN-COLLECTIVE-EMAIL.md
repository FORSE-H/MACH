# Open Collective — Fiscal Sponsorship Guide & Outreach

## What Open Collective is

Open Collective is a platform that lets open-source projects receive
donations and grants legally without setting up their own legal entity.
The "Open Source Collective" is their fiscal host for open-source projects.

They hold the money on your behalf, handle invoices and payments, and
take a 5% fee. You get a public page showing all income and expenses —
full financial transparency, which open-source funder, OS4Science, and other funders
require.

URL: https://opencollective.com/opensource
Apply: https://opencollective.com/create (select "Open Source Collective" as host)

---

## Step 1 — Apply for fiscal hosting (do this first, before any email)

Go to https://opencollective.com/create and:
- Name: MACH — Machine-Actionable Catalog for Healthcare
- Description: One paragraph about the project
- GitHub: https://github.com/FORSE-H/MACH
- Select fiscal host: Open Source Collective
- They approve most open-source projects within a few days

Once approved you get a page like:
https://opencollective.com/mach-healthcare-catalog

---

## Step 2 — Email to Open Collective (after you have your page)

This is NOT a grant application. Open Collective is not a funder.
This email is to introduce MACH and explore if they want to feature
it or connect you with their network. It's relationship-building, not asking.

---

**To:** hello@oscollective.org
**Subject:** New fiscal hosted project — MACH, open healthcare AI catalog

---

Hi Open Source Collective team,

I wanted to introduce a project I have just set up under Open Source
Collective fiscal hosting: MACH — Machine-Actionable Catalog for
Healthcare (https://opencollective.com/[your-slug]).

MACH is an open, machine-actionable catalog of open-source healthcare
software, AI/ML models, clinical standards, and MCP servers. Every entry
is a structured JSON-LD file aligned with DCAT-AP, MLDCAT-AP 3.0, and
CodeMeta 3.0 — making the catalog queryable by both humans and AI agents.
The catalog lives at https://github.com/FORSE-H/MACH and the live site
is at https://forse-h.github.io/MACH.

The project was conceptualised in October 2025. We submitted an open-source funder
open-source funding application in May 2026 (reference ) and
are awaiting a decision. Open Source Collective fiscal hosting will be
the legal home for the project as we build toward additional funding
from sources like OS4Science and Sovereign Tech Fund.

I wanted to reach out for two reasons:

1. If MACH aligns with any featured projects or newsletters you run
   for the open-source health/science space, I would love to be
   considered when the time is right.

2. I am a solo founder building this without institutional backing.
   If you have resources, community managers, or peer connections
   in the open health data or life sciences open source space who
   might be interested in MACH as a catalog entry or as a contributor,
   I would be grateful for any introductions.

The catalog is CC-BY-4.0, the code is Apache-2.0, and all editorial
decisions are governed by a public conflict-of-interest policy. It is
built to be independently sustainable — infrastructure costs are near
zero (static site, Git as database) and the value is in the curation
and machine-readable exports.

Thank you for what you do for the open-source community.

Best regards,
Priyanka Ojha
Founder, MACH
ORCID: [your ORCID]
LinkedIn: [your LinkedIn]
GitHub: https://github.com/FORSE-H

---

## Step 3 — What to do if/when open-source funder approves the grant

open-source funder will want to pay via invoice to a legal entity. With Open Source
Collective as fiscal host, the flow is:

1. open-source funder sends grant money to Open Source Collective
2. Open Source Collective holds it in your MACH collective balance
3. You submit expenses (invoices for your time at EUR 150/hr) via the
   Open Collective platform
4. Open Source Collective pays you after approving the expense
5. 5% fee is deducted from the collective balance

This is clean, transparent, and exactly how dozens of funded
open-source projects handle payment.

When you reach out to open-source funder after grant approval, tell them:
"The fiscal host for MACH is Open Source Collective
(opencollective.com/opensource). Payment should be made to Open Source
Collective Inc. with reference to the MACH collective."

---

## Step 4 — What to write to OS4Science when applying in 2027

At that point you will have:
- Fiscal host: Open Source Collective (or NumFOCUS)
- open-source funder grant completed with deliverables
- 100+ catalog entries
- Measurable community traction

Frame the OS4Science application around the PYTHON FDP SERVER
(github.com/FORSE-H/mach-fdp) as Track 2 Foundational Libraries —
a reusable Python implementation of the FAIR Data Point specification
that any life sciences catalog can use. Not the catalog itself (which
they explicitly say is out of scope as "repository infrastructure")
but the underlying server library.

That framing maps perfectly to their stated priorities:
- Foundational library used across multiple projects
- Unlocks AI-native workflows (FDP serves DCAT RDF to agents)
- Interoperability framework (FDP protocol is a standard)
- Not a prototype — built on top of proven MACH catalog work
