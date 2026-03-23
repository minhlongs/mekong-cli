# Binh Phap Master — The Art of Command

> *"The general who wins makes many calculations before battle."* — Sun Tzu

This document maps Sun Tzu's 13 chapters to Mekong CLI's command system.
Every command is a weapon. Every workflow is a battle plan.
OpenClaw dispatches commands like a general commanding armies.

---

## The 13 Chapters → 5 Layers → 300+ Commands

```
CHAPTER          LAYER           PURPOSE              KEY COMMANDS
─────────────────────────────────────────────────────────────────
1. Calculations  Founder         Assess before acting  /swot /annual /validate
2. Waging War    Business        Resource management   /finance /budget /pricing
3. Strategic     Product         Win without fighting   /plan /brainstorm /scope
   Attack
4. Disposition   Engineering     Unbreakable position   /cook /code /test /review
5. Momentum      Business        Force multiplication   /marketing /sales /growth
6. Void &        Product         Exploit weaknesses     /competitive /research
   Substance
7. Maneuvering   Engineering     Speed of execution     /deploy /fix /hotfix
8. Nine          Ops             Adapt to situation     /debug /incident /rollback
   Variations
9. The March     Engineering     Steady progress        /sprint /milestone /standup
10. Terrain      Business        Know your market       /market /tam /positioning
11. Nine         Founder         Critical situations    /fundraise /pivot /crisis
    Situations
12. Fire Attack  Business        Decisive strikes       /launch /campaign /outreach
13. Intelligence Ops             Know before acting     /audit /scout /health
```

---

## Chapter 1: Calculations (始計) — ASSESS BEFORE ACTING

> *"War is a matter of vital importance. It must be studied."*

**Layer:** Founder | **When:** Before starting ANY project or major decision.

| Command | Purpose | MCU |
|---------|---------|-----|
| `/swot` | Strengths, Weaknesses, Opportunities, Threats | 2 |
| `/annual` | Annual business plan with financials | 3 |
| `/founder:validate` | PMF, unit economics, market validation | 5 |
| `/okr` | Set measurable objectives | 2 |
| `/venture:five-factors` | Dao-Tian-Di-Jiang-Fa assessment | 3 |

**OpenClaw dispatch rule:** Before any project exceeding 10 MCU, run `/swot` first.

---

## Chapter 2: Waging War (作戰) — RESOURCE MANAGEMENT

> *"When you engage in actual fighting, if victory is long in coming, men's weapons will grow dull."*

**Layer:** Business | **When:** Managing budget, runway, and operational costs.

| Command | Purpose | MCU |
|---------|---------|-----|
| `/finance` | Financial overview and tracking | 2 |
| `/budget` | Budget allocation and monitoring | 2 |
| `/pricing` | Pricing strategy analysis | 3 |
| `/finance:monthly-close` | Revenue reconcile, P&L, cash flow | 5 |
| `/studio:allocate` | MCU budget reallocation | 2 |

**OpenClaw dispatch rule:** Check `/finance` before committing to any expense > 5 MCU.

---

## Chapter 3: Strategic Attack (謀攻) — WIN WITHOUT FIGHTING

> *"Supreme excellence consists in breaking the enemy's resistance without fighting."*

**Layer:** Product | **When:** Planning features, finding elegant solutions.

| Command | Purpose | MCU |
|---------|---------|-----|
| `/plan` | Implementation plan with phases | 3 |
| `/brainstorm` | Explore solutions with trade-off analysis | 2 |
| `/scope` | Define boundaries, prevent scope creep | 2 |
| `/product:discovery` | Problem → persona → solution → validation | 5 |
| `/ask` | Technical consultation (zero-cost intel) | 0 |

**OpenClaw dispatch rule:** Always `/plan` before `/cook`. Planning prevents rework.

---

## Chapter 4: Disposition (軍形) — UNBREAKABLE POSITION

> *"The good fighters of old first put themselves beyond the possibility of defeat."*

**Layer:** Engineering | **When:** Building quality, defensive code, test coverage.

| Command | Purpose | MCU |
|---------|---------|-----|
| `/cook` | End-to-end feature implementation | 3-5 |
| `/code` | Focused code changes | 1-3 |
| `/test` | Run and validate test suites | 1 |
| `/review` | Code quality assessment | 2 |
| `/fix` | Debug with root cause analysis | 2 |

**OpenClaw dispatch rule:** Every `/cook` MUST end with `/test` + `/review`. No exceptions.

**PEV cycle:** Plan → Execute → Verify. If verify fails → self-heal → retry.

---

## Chapter 5: Momentum (兵勢) — FORCE MULTIPLICATION

> *"The onset of troops is like the rush of a torrent."*

**Layer:** Business | **When:** Amplifying reach, creating viral growth.

| Command | Purpose | MCU |
|---------|---------|-----|
| `/marketing` | Marketing strategy and execution | 3 |
| `/sales` | Sales pipeline and outreach | 3 |
| `/growth:experiment` | Design and run growth experiments | 3 |
| `/content` | Content creation pipeline | 2 |
| `/launch` | Product launch orchestration | 5 |

**OpenClaw dispatch rule:** Never launch without `/marketing` + `/sales` in parallel.

---

## Chapter 6: Void & Substance (虛實) — EXPLOIT GAPS

> *"Appear where you are not expected."*

**Layer:** Product | **When:** Competitive analysis, finding market gaps.

| Command | Purpose | MCU |
|---------|---------|-----|
| `/research` | Deep technical/market research | 3 |
| `/competitive` | Competitor analysis and battlecards | 3 |
| `/venture:void-substance` | Find where competitors are hollow | 3 |
| `/scout` | Fast codebase/market reconnaissance | 1 |

**OpenClaw dispatch rule:** Run `/competitive` quarterly. Know where rivals are weak.

---

## Chapter 7: Maneuvering (軍爭) — SPEED OF EXECUTION

> *"Let your rapidity be that of the wind."*

**Layer:** Engineering | **When:** Rapid deployment, hotfixes, time-critical shipping.

| Command | Purpose | MCU |
|---------|---------|-----|
| `/deploy` | Production deployment | 3 |
| `/fix` | Rapid bug resolution | 2 |
| `/release:hotfix` | Emergency fix → test → deploy | 3 |
| `/release:ship` | Full release cycle | 5 |

**OpenClaw dispatch rule:** Hotfixes bypass normal review cycle. Speed > process when production is down.

---

## Chapter 8: Nine Variations (九變) — ADAPT TO SITUATION

> *"Do not repeat the tactics which have gained you one victory."*

**Layer:** Ops | **When:** Incidents, unexpected failures, changing conditions.

| Command | Purpose | MCU |
|---------|---------|-----|
| `/debug` | Systematic root cause analysis | 2 |
| `/sre:incident` | Incident triage and response | 3 |
| `/devops:rollback` | Emergency rollback to last known good | 3 |
| `/ops:health-sweep` | System-wide health audit | 3 |

**OpenClaw dispatch rule:** On incident: `/debug` first, then decide `/fix` or `/devops:rollback`.

---

## Chapter 9: The March (行軍) — STEADY PROGRESS

> *"Move not unless you see an advantage."*

**Layer:** Engineering | **When:** Sprint execution, daily progress tracking.

| Command | Purpose | MCU |
|---------|---------|-----|
| `/sprint` | Sprint planning and execution | 3 |
| `/standup` | Daily progress report | 1 |
| `/milestone` | Track milestone completion | 2 |
| `/backlog` | Prioritize and groom backlog | 2 |

**OpenClaw dispatch rule:** Start each day with `/standup`. End each sprint with `/retro`.

---

## Chapter 10: Terrain (地形) — KNOW YOUR MARKET

> *"Know the terrain, know the weather, and your victory will be complete."*

**Layer:** Business | **When:** Market analysis, positioning, pricing decisions.

| Command | Purpose | MCU |
|---------|---------|-----|
| `/market` | Market analysis and sizing | 3 |
| `/venture:terrain` | Sun Tzu terrain analysis for markets | 3 |
| `/positioning` | Brand positioning strategy | 2 |
| `/tam` | Total Addressable Market sizing | 2 |

**OpenClaw dispatch rule:** Before entering new market, run `/venture:terrain` + `/tam`.

---

## Chapter 11: Nine Situations (九地) — CRITICAL MOMENTS

> *"On desperate ground, fight."*

**Layer:** Founder | **When:** Fundraising, pivots, existential decisions.

| Command | Purpose | MCU |
|---------|---------|-----|
| `/fundraise` | Full fundraise preparation | 5 |
| `/founder:negotiate` | Term sheet analysis + dilution modeling | 4 |
| `/founder:validate` | Business model validation before spending | 5 |
| `/pivot` | Strategic direction change | 3 |

**OpenClaw dispatch rule:** Fundraise = all-in. Run `/founder:raise` super command (8 agents parallel).

---

## Chapter 12: Fire Attack (火攻) — DECISIVE STRIKES

> *"There are five ways of attacking with fire."*

**Layer:** Business | **When:** Launches, campaigns, concentrated marketing pushes.

| Command | Purpose | MCU |
|---------|---------|-----|
| `/campaign` | Multi-channel marketing campaign | 5 |
| `/outreach` | Sales outreach blast | 3 |
| `/launch` | Coordinated product launch | 5 |
| `/growth:channel-optimize` | Channel audit and optimization | 3 |

**OpenClaw dispatch rule:** Fire attacks require preparation. Never `/launch` without completing Chapters 1-5 first.

---

## Chapter 13: Intelligence (用間) — KNOW BEFORE ACTING

> *"What enables the wise sovereign to strike and conquer is foreknowledge."*

**Layer:** Ops | **When:** Monitoring, auditing, gathering intelligence.

| Command | Purpose | MCU |
|---------|---------|-----|
| `/audit` | Comprehensive system audit | 3 |
| `/scout` | Fast reconnaissance | 1 |
| `/health` | System health check | 1 |
| `/status` | Current state overview | 0 |
| `/security` | Security posture assessment | 3 |

**OpenClaw dispatch rule:** `/health` runs automatically. `/audit` runs weekly. `/security` runs before any deploy.

---

## Command Composition Rules

### Sequential Chains (must complete in order)
```
Chapter 1 → Chapter 3 → Chapter 4 → Chapter 13
/swot → /plan → /cook → /audit
"Calculate, plan, build, verify."
```

### Parallel Dispatches (independent, run simultaneously)
```
Chapter 5 + Chapter 12 + Chapter 6
/marketing + /launch + /competitive
"Attack on all fronts while scouting."
```

### Emergency Protocol
```
Chapter 8 → Chapter 7
/sre:incident → /release:hotfix
"Adapt, then strike fast."
```

### Growth Loop
```
Chapter 9 → Chapter 10 → Chapter 5 → Chapter 12 → Chapter 13
/sprint → /market → /growth → /launch → /audit → (repeat)
"March, survey terrain, build momentum, strike, gather intel."
```

---

## OpenClaw Dispatch Matrix

OpenClaw uses this matrix to decide which chapter's commands to invoke:

| Situation | Chapter | Primary Command | Fallback |
|-----------|---------|----------------|----------|
| New project | 1 | `/swot` | `/ask` |
| Feature request | 3 → 4 | `/plan` → `/cook` | `/brainstorm` |
| Bug report | 8 → 7 | `/debug` → `/fix` | `/rollback` |
| Revenue down | 10 → 5 | `/market` → `/marketing` | `/pricing` |
| Fundraising | 11 | `/founder:raise` | `/pitch` |
| Launch day | 12 | `/launch` | `/campaign` |
| Security alert | 13 → 8 | `/security` → `/incident` | `/audit` |
| Daily ops | 9 | `/standup` | `/status` |
| Low budget | 2 | `/finance` | `/budget` |

---

*"The art of war teaches us not to rely on the likelihood of the enemy not coming, but on our own readiness to receive him."*

**This is our DNA. Commands are weapons. Chapters are strategy. OpenClaw is the general.**
