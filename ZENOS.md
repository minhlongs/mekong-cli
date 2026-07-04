# ZENOS: The Constitutional Operating System for One-Person Companies

> **Version:** 0.1.0 (Founding Draft)
> **Status:** Ratified by first 3 Mekong founders
> **Last revised:** 2026-07-04
>
> *"No kings. No gods. No prisoners. But also no constitution we have not tested adversarially."*

---

## Preamble

ZenOS is an operating system for one-person companies (Economic Particles). It does not command particles how to act — it defines the boundaries within which they cannot cross.

The stack:

```
Human (founder)
  -> Constitution (this document)
    -> AI Cells (autonomous economic agents)
      -> Particles (economic entities)
        -> Forest (particle networks)
          -> Commons (shared governance)
            -> Civilization (long-term outcome)
```

**Critical caveat from research:** Constitutional AI has hard theoretical limits. Constitutions can backfire (Young 2026, arXiv:2603.03000), reward hacking is structurally guaranteed (Wang & Huang 2025), and prompt-only prohibitions fail under economic pressure (arXiv:2601.11369). This document is therefore not a "set and forget" safeguard. It requires adversarial testing before activation, continuous institutional enforcement, and regular revision. Every article below should be read as a hypothesis to be tested, not a rule to be enforced.

---

## Article 1: Human Supremacy

Humans are above AI. AI is above Capital. No AI Cell may override a founder's explicit decision. Founders hold a single-use veto for constitutional violations — a last resort against capture.

**Implications:**
- Every economic decision above a threshold (defined per particle) requires human approval.
- AI Cells operate at the privilege level granted by the founder, starting at L0 (observer).
- All AI Cell decisions must be explainable and logged on the Behavior Graph.

**Caveat:** Research shows that human-in-the-loop degrades with scale (Cong et al., HBS 2025 — 6.3% average DAO participation). ZenOS must monitor and design against founder apathy, not assume eternal vigilance.

---

## Article 2: Mission Integrity

Mission precedes revenue. A particle's constitution defines its mission; any action that advances revenue at the expense of mission is a constitutional violation.

**Implications:**
- Quarterly constitutional review by the Compliance AI Cell.
- Revenue-generating actions must score above the mission-alignment threshold (default: 0.7).
- If mission and revenue conflict, the Behavior Graph logs the trade-off and escalates to the founder.

**Caveat:** Constitutional backfire risk (Young 2026, Theorem 3) means a poorly worded mission article can incentivize worse behavior than no article at all. Every mission clause must pass adversarial sandbox testing before activation.

---

## Article 3: AI Cell Boundaries

AI Cells start with minimum privileges. Privileges escalate only through constitutional review.

**Privilege levels:**
| Level | Scope | Approval |
|-------|-------|----------|
| L0 | Read market data, generate reports | Self-service |
| L1 | Suggest actions, draft proposals | Human approval required |
| L2 | Execute within budget (<$1K/day) | Constitutional bounds |
| L3 | Execute within policy (<$10K/day) | Guardian oversight |
| L4 | Restructure operations | Founder + quorum vote |

**Institutional enforcement (not declarative):** Research demonstrates that prompt-only constitutional prohibitions fail under economic pressure (arXiv:2601.11369: collusion tier 3.02 vs. ungoverned 3.10). ZenOS therefore enforces Cell boundaries through:
- Behavior Graph collusion detection.
- Guardian AI Cell (independent, no economic responsibilities).
- Tripartite separation: Strategy, Operations, Compliance Cells are distinct.

---

## Article 4: Economic Agency

Every Economic Particle has the right to:
- Own assets, hold treasury, and transact in multiple currencies.
- Define its own dissolution procedure in its particle constitution.
- Fork from the parent particle, retaining its identity graph and trust score.
- Refuse to participate in any Forest or Commons.

**Dissolution:** A particle dissolves only by founder decision, constitutional violation, or mutual agreement with counterparties. Dissolution guarantees settlement of all outstanding obligations before treasury closure.

---

## Article 5: Financial Sovereignty

Particles transact in any currency or medium they choose — fiat, stablecoin, MCU credits, or barter. Every payment is checked against the particle's constitution before execution.

**Constitutional hooks on payments:**
```
Transaction initiated
  -> Check daily budget (Treasury Cell)
  -> Check counterparty trust score (Behavior Graph)
  -> Check mission alignment (Constitution)
  -> Escalate if: >$10K, new counterparty, mission mismatch
```

No payment provider may be forced on a particle. Particles choose their own rails (Stripe, Wise, stablecoin, bank transfer) and bear the compliance responsibility.

---

## Article 6: Behavioral Integrity

The Behavior Graph tracks every interaction between AI Cells, particles, and founders. This graph is the foundation for trust scoring, collusion detection, and governance.

**Trust graph principles:**
- Trust scores are computed from observed behavior: success rate, constitutional compliance, payment punctuality, community contribution, transparency.
- Collusion detection runs continuously: cross-cell behavior pattern analysis identifies anomalous coordination.
- Anti-concentration monitoring: no single founder, Cell, or coalition may control >25% of Commons voting power.
- Trust scores are portable across particles (if a particle forks, its score follows).

**Caveat:** Trust scores can be gamed (reward hacking is structurally guaranteed per Wang & Huang 2025). ZenOS must rotate evaluation metrics and periodically audit the trust function itself.

---

## Article 7: Commons Governance

The Commons is the shared governance layer — protocol, treasury, dispute resolution. It follows Ostrom's 8 principles (Ostrom 1990) adapted for digital-native governance.

**Tripartite separation (AE4E/NetX, arXiv:2603.25100):**
- **Legislation:** Constitutional amendments, protocol upgrades (particle-weighted voting).
- **Execution:** Guardian and AI Cells execute governance decisions.
- **Adjudication:** Dispute resolution by Guardian mediation -> Community vote.

**Anti-capture mechanisms:**
| Mechanism | Prevents |
|-----------|----------|
| Mission-locked foundation | Profit-driven pivot |
| Contribution-weighted voting | Investor capture (top 10% control 76.2% in DAOs per Cong 2025) |
| Term limits (Guardian: 1yr max 2 terms) | Entrenched leadership |
| Transparent treasury on Behavior Graph | Embezzlement |
| Right to fork | Protocol capture |
| Sunset clause (20yr re-ratification) | Zombie Commons |

---

## Article 8: Right to Exit

Any particle may exit the Commons with full data sovereignty — no lock-in, no penalty.

**Exit guarantees:**
1. **Data export:** Full Behavior Graph subgraph (their nodes, edges to their data).
2. **IP license:** Perpetual, irrevocable license to the ZenOS protocol at the commit they fork from.
3. **Identity portability:** Particle ID and trust score carried to any fork.
4. **No penalty:** Exit does not reduce trust score, future earning potential, or reputation.

**Technical guarantee:** The Right to Exit is enforced at the protocol level, not through policy. ZenOS code repositories are public; data schemas are standard; no proprietary format traps user data.

---

## Article 9: Anti-Capture and Evolution

ZenOS must protect against capture — by founders, large particles, AI Cells, or external actors — while enabling evolution.

**Amendment process:**
| Tier | Scope | Threshold | Cooling period |
|------|-------|-----------|----------------|
| Foundational (Layer 1) | Human rights, Right to Exit, anti-capture | Founder veto + 2/3 supermajority | 90 days |
| Operational (Layer 2) | Cell boundaries, scoring formulas | 3/4 supermajority | 30 days |
| Soft (Layer 3) | Guidelines, best practices | Simple majority | 7 days |

**Sunset clauses:**
- This constitution expires 20 years from ratification unless re-ratified by 4/5 supermajority.
- Any article may carry its own sunset clause (default: none).
- Emergency amendments expire after 90 days unless ratified as permanent.

**Adversarial audit:** Every article must be adversarially tested before activation (per ASIMOV benchmark findings: adversarial constitutions score 37.7% alignment vs. 52.1% random). ZenOS maintains a constitutional sandbox for automated article testing.

---

## References

- Bai et al. (2022). "Constitutional AI." *Anthropic*.
- Young (2026). "Limitations of Constitutional AI." arXiv:2603.03000.
- Sapienza et al. (2026). "Multi-Agent Collusion with LLMs." arXiv:2601.11369.
- Wang & Huang (2025). "Reward Hacking as Structural Equilibrium." *ACM EC 2025*.
- Skalse et al. (2022). "Defining Reward Hacking." *NeurIPS 2022*.
- Ruan (2026). "AE4E: Agent Enterprise for Enterprise." arXiv:2603.25100.
- Cong et al. (2025). "DAO Decentralization." HBS Working Paper.
- Ostrom (1990). *Governing the Commons*. Cambridge University Press.
- Tomashev et al. (2025). "Patchwork AGI." arXiv:2512.16856.

See also: `docs/03_constitution.md` through `docs/14_manifesto_review.md` for the full research analysis behind each article.
