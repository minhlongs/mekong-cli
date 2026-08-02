# ZenOS Commons Charter — v0.1

> **Status:** Proposed — Pending Founders Ratification
> Ratification threshold (Art 9 L1): Founder veto + 2/3 supermajority
> Cooling period: 90 days before vote opens
> **Created:** 2026-07-06 | **Last revised:** 2026-07-06
> **Authority:** ZENOS Art 7 (Commons Governance), Art 9 (Amendment Process)
> **Zone:** QUÂN DOANH — this file is the ZenOS Constitution's governance layer
> **Supersedes:** `docs/zenos-commons.md` (V0.1 draft, now archived as historical)

## Preamble

The ZenOS Commons governs protocol upgrades, treasury allocation, dispute resolution,
and constitutional amendments within the mekong-cli ecosystem. It exists to prevent
capture — by founders, large contributors, or external actors — while enabling evolution.

Per ZENOS Art 9, this charter expires 20 years from ratification unless re-ratified by
a 4/5 supermajority. Whenever ZENOS.md and ZENOS-COMMONS.md conflict, ZENOS.md ("Human
Supremacy" Art 1) wins on human-rights and anti-capture articles.

---

## Article 1: Membership Tiers

| Tier | Base Voting | Description | Eligibility |
|------|-------------|-------------|-------------|
| **Founder** | 1 base vote, no contribution multiplier | Holds residual veto on foundational amendments (ZENOS Art 9) | Founder signature on ratification |
| **Contributor** | 1 base vote + contribution bonus (≤ 5×) | Code, docs, governance work | ≥ 1 accepted contribution |
| **Holder** | 1 base vote, contribution-weighted future | Stakeholders (token/license-holders) | Defined in operational tier |

**Contribution formula (v1, subject to L2 amendment):**

```
voting_power = 1.0 + min(commit_count^0.5, 10.0)
capped at 5× = max(voting_power, 5.0)
```

Where `commit_count` is the count of non-merge-commit authored entries in the git log
since the partner's onboarding date. Adapted from `docs/zenos-commons.md` (v0.1 draft).

**Anti-concentration cap:** No single member may control > 25% of total voting power.
Enforced at registry write time — `MemberRegistry.register()` raises `ConcentrationError`
if the addition would push `member.voting_power / total > 0.25`.

**Founder trim:** Founders default to 1 base vote regardless of contribution count, but
their veto does not count toward the 25% concentration cap.

---

## Article 2: Tripartite Separation

Per ZENOS Art 7, the Commons enforces the Separation of Powers through three branches,
mirroring AE4E/NetX cit. (Ruan 2026, arXiv:2603.25100):

| Branch | Scope | Voting weight | Who participates |
|--------|-------|--------------|------------------|
| **Legislation** | Constitutional amendments, protocol upgrades | Per Art 1 contribution formula | All active members |
| **Execution** | Guardian + AI Cells execute approved proposals | Guardian 1×, each AI Cell 0× (no vote) | Guardian, Execution AI Cell |
| **Adjudication** | Dispute resolution | Guardian mediates → Community vote if unresolved | Guardian (binding under L1/L2) |

No member or Cell may occupy two branches simultaneously. Guardian is the single
bridge — it Executes and mediates Adjudication, but only votes on Legislation under
delegated authority.

---

## Article 3: Proposal Types & Thresholds

Aligned to ZENOS Art 9 3-tier system. Every proposal must declare a tier at submission.
Self-declared soft proposals may be escalated by 5% of veto-holding members.

| Tier | Scope examples | Threshold | Cooling period | Voting window | Quorum |
|------|---------------|-----------|----------------|--------------|--------|
| **L1 — Foundational** | Human rights amendments, Art 1 changes, Right to Exit, anti-capture regenesis | Founder veto + 2/3 supermajority of weighted votes | 90 days | 14 days | 2/3 of eligible votes |
| **L2 — Operational** | Cell boundaries, scoring formulas, treasury allocation rules, quorum updates | 3/4 supermajority of weighted votes | 30 days | 14 days | 1/2 of eligible votes |
| **L3 — Soft** | Guidelines, best practices, minor process changes | Simple majority of weighted votes | 7 days | 7 days | 1/3 of eligible votes |

**Emergency amendments:** L2/L3 scope only. Auto-expire 90 days after enactment unless
ratified as permanent through the standard tier path. Emergency amendments cannot modify
L1 foundational articles.

**Quorum floor amendment:** With < 10 active members, the minimum quorum floor is
`ceil(member_count / 2)` instead of the absolute table minimum. This transition rule
automatically expires when active members ≥ 10.

---

## Article 4: Voting Mechanics

**Vote lifecycle:**

```
DRAFT (author only)
  → ACTIVE (cooling completes, voting window opens)
    → PASSED (quorum + threshold met) → ENACTED
    → FAILED (threshold not met or quorum failed) → ARCHIVED
    → EXPIRED (window closes with insufficient votes) → ARCHIVED
    → CANCELLED (author withdraws before voting starts) → ARCHIVED
```

**Vote recording:** Each vote carries `member_id + proposal_id + choice + timestamp`.
The `vote_engine` appends a SHA-256 chain across all votes for the proposal id, enabling
deduplication and audit without revealing member-vote association (ballot privacy).

**Founder override:** When `commons_member_count < 3`, every proposal automatically
enters `_FOUNDER_REVIEW` state after the cooling period. Founder may approve, reject, or
send back for revision. This bypass expires when member count ≥ 3.

**Right to Abstain:** A member may abstain by submitting a recorded timestamp without
a choice. Abstentions count toward quorum but not toward either threshold total.

---

## Article 5: Treasury Management

**Storage:** Database-backed ledger (see `src/mekong/treasury/`). Off-chain only per
ZENOS Art 5 ("No payment provider may be forced on a particle").

**Allocation rules (default, v1):**

| Bucket | Share | Use |
|--------|-------|-----|
| operating_reserve | 30 % | Day-to-day operations |
| tax_reserve | 25 % | Regulatory compliance |
| reinvestment | 30 % | Protocol development |
| founder_draw | 15 % | Founder distribution (Art 1: Human Supremacy) |

Allocation is applied on every incoming transaction; splitting is automatic.

**Withdrawal approval:**

| Amount | Required approval |
|--------|-------------------|
| ≤ treasury_threshold (configurable, default: $5,000) | Guardian (L2) |
| > threshold, ≤ 10× threshold | L2 supermajority |
| > 10× threshold | L1 supermajority + founder veto |

Treasury is dormant until explicit funding source is set by user decision (DECISION 3
in the Track F plan).

---

## Article 6: Anti-Capture Mechanisms

| Mechanism | Enforced by | Triggers |
|-----------|------------|----------|
| Anti-concentration cap (Art 1, ≤ 25 % per member) | `MemberRegistry.register()` | Hard fail on insert |
| Term limits — Guardian: 1 year max, 2 terms | `term_limits.py` | Locks L1/L2 execution when out of term |
| Right to fork (Art 8, 30-day notice) | `fork.py` (F3) | 30-day timer on `mekong commons fork` |
| Foundation safeguard | Amendment enforcer | Founder veto + 2/3 L1 — prevents pivot |
| Sunset clause — 20-year re-ratification | `sunset_tracker.py` (F3) | Annual reminder; expires if no re-ratification |
| Transaction ledger — append-only | `treasury/ledger.py` | Every entry chained; delete blocked |
| Contribution-weighted voting | `member_registry.compute_power()` | commit log driven; resistant to token-gaming |

Verbose implementation references live in Waves F2 and F3 of the Track F plan.

---

## Article 7: Right to Exit (Redundant with ZENOS Art 8)

Restated here for completeness — ZENOS.md Art 8 is the single authoritative text.
This Article confirms: every member or particle may exit the Commons with full data
sovereignty, no lock-in, no penalty. Exit is protocol-enforced (code drives it), not
policy-enforced.

---

## Article 8: Definitions

| Term | Definition |
|------|-----------|
| **Active member** | Status = ACTIVE, not suspended, term current, voting weight > 0 |
| **Agent** | `mekong` executor, Subagent, AI Cell under ZENOS Art 3 |
| **Constitution** | `mekong/constitution/ZENOS.md` + this `ZENOS-COMMONS.md` together |
| **Contribution** | Git-authored non-merge commit in the mekong-cli repo, or accepted doc/design work |
| **Eligible vote** | Vote from an active member counted toward threshold |
| **Emergency amendment** | L2/L3 only; auto-expires 90 days |
| **Guardian** | Execution-branch operator; term-limited to 1yr, 2 terms |
| **Member** | A person or entity enrolled in the Commons member registry |
| **Proposal** | A structured change request to this charter or any L2/L3 config |
| **Tier** | L1/L2/L3 proposal tier per Art 3 |
| **Treasury** | Commons funds, per Art 5 |

---

## Article 9: Amendment Routing — Self-Modification

This charter may be amended only through the procedures in this Article. To prevent
infinite-amendment loops, L2/L3 migrations cannot modify Art 9 itself — only Art 1
"Founder veto + 2/3 supermajority" path can modify this article's quorum/threshold values.

**Amendment engine:** See `src/mekong/constitution/amendment.py` and `amendment_enforcer.py` (F3).

**Cooling period enforcement:** Proposals in the cooling window may not be voted on. The
cooling timer starts at proposal submission; early votes are rejected with `CoolingError`.

**Veto scope (ZENOS Art 1):** The founder retains a single-use veto on any L1 amendment
deemed a constitutional violation. The veto must describe the violating clause and is
logged on the behavior graph. Founders may not veto L3 amendments unless they escalate
to L1 scope (which triggers the L1 threshold).

---

## Article 10: Transition & Ratification

**Current status:** Draft pending Votes. No amendment is binding until F2 voting is
operational (commons_member_count ≥ 3) and the founder exercises the Art 9 ratification path.

**First 5 provisions that require founding resolution:**
1. Initial member list (DECISION 5 in plan)
2. Contribution formula (DECISION 1)
3. Treasury seed source (DECISION 3)
4. Withdrawal threshold (DECISION 4)
5. Guardian election procedure (DECISION 6)

Until these are resolved via founder ratification, the following operational defaults apply:
- All proposals require founder approval (`member_count < 3` gate)
- `treasury_threshold` defaults to $5,000 (configured in `allocation.py`)
- No automatic Guardian election — founder acts as default Guardian
