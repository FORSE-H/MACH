# Governance

MACH is an editorially independent open-source project. This document describes how decisions
are made and how the catalog maintains its integrity.

---

## Editorial independence

Sponsorships, donations, and partnerships have **no influence** on editorial decisions.
No sponsor, partner, or funder may request that an entry be added, upgraded, downgraded,
or removed. Violations of this principle are grounds for immediate removal of the sponsor
relationship and public disclosure.

---

## Roles

### Founder / Lead Curator
Currently: the founding maintainer (see repo). Responsible for final editorial decisions,
release management, and fiscal oversight.

### Curators
Individuals with merge rights who review and approve PRs. Curators are nominated by the
lead curator and accepted by simple majority of existing curators. A curator may be removed
by a two-thirds majority vote for sustained inactivity (>6 months) or breach of this policy.

### Contributors
Anyone who submits a pull request. No special rights. All contributions welcome.

---

## Decision-making

**Routine entries** (new entry, minor update): any single curator may approve and merge,
provided the entry checklist in CONTRIBUTING.md is satisfied.

**Judgement changes** (upgrading or downgrading an existing entry): requires a second
curator's approval or a 7-day comment period with no objection from the community.

**Policy changes** (changes to this document, CONTRIBUTING.md, or the data schema):
requires a public PR open for at least 14 days, a comment period, and approval from the
lead curator.

**Removal of an entry**: requires a documented reason (entry is now proprietary, project
is abandoned, safety concern) and approval from the lead curator.

---

## Conflict of interest policy

Any curator who has a financial, employment, or personal relationship with an organisation
behind an entry **must** disclose this before reviewing that entry and **must not** be the
sole approver of a decision affecting that entry.

Disclosures are made in the PR thread and are permanently part of the Git history.

---

## Appeal process

If a contributor believes an editorial decision (inclusion, exclusion, or judgement level)
is incorrect or biased, they may:

1. Open a GitHub Issue labelled `appeal` with a clear evidence-based argument.
2. The lead curator will respond within 14 days with a reasoned decision.
3. If the appellant remains unsatisfied, the matter is put to a vote of all active curators.
4. The majority vote is final.

---

## Fiscal policy

MACH is currently an unincorporated community project. All financial relationships
(grants, sponsorships, donations) are disclosed publicly in the [SUPPORTERS.md](SUPPORTERS.md)
file, including amounts and dates.

The long-term goal is fiscal sponsorship under a neutral home (LF Public Health,
LF AI & Data, or Open Collective). This document will be updated when that transition occurs.

---

## Code of conduct

This project follows the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md).
Violations may be reported to the lead curator.
