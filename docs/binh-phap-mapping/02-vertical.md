# Phần 2: Vertical Dispatch — 3D Topology Engine

> Status: DRAFT

## 1. Brainstorm Contract (reuse P1)
Outcome: Document vertical dispatch flow with module ownership, command sequence, Jidoka hooks.
Constraints: (1) Chain ordered/synchronous (2) Per-command timeout+retry (3) Failure stops chain (4) Jidoka auto-fix before escalation
Non-goals: (1) No parallel in vertical (horizontal handles that) (2) No MRR tracking (diagonal handles that)
Acceptance: Sequence diagram + module owner table + 3 Jidoka hook points

## 2. Current State
Chain: swot -> plan -> cook -> test -> deploy -> audit
Hardcoded in topology.py::get_vertical_chain()
Pain: no per-company config, no timeout/retry, no Jidoka hooks between steps

## 3. Proposed Architecture

### Vertical Dispatch Flow
  BinhPhapDispatcher.next_action()
        |
        v
  [1] Read chain from state
  [2] Get next command
  [3] Resolve recipe/skill path
  [4] Resolve LLM provider (Fable/Opus)
  [5] Execute via PEV orchestrator
  [6] Jidoka inspect output
  [7] Auto-fix if recoverable
  [8] advance_vertical(result)
  [9] Save state -> next loop

### Module Owner Table
| Step | Module | Responsible | Timeout |
|------|--------|-------------|---------|
| SWOT | src/core/competitive_intel.py (NEW) | Strategy agent | 60s |
| Plan | src/cli/idea_commands.py | Idea pipeline | 120s |
| Cook | src/cli/cook_command.py | Engineering | 180s |
| Test | src/cli/sdlc/code.py | QA agent | 120s |
| Deploy | src/cli/sdlc/deploy.py | DevOps | 180s |
| Audit | src/daemon/jidoka.py | Jidoka monitor | 60s |

### Jidoka Hook Points (3)
1. POST-COOK: scan output for breaking changes -> auto-fix or escalate
2. POST-TEST: if test failures -> run test --updateSnapshot or escalate
3. POST-DEPLOY: rollback on failure via git revert HEAD

## 4. Trade-off
| A: Inline chain | B: State machine | C: Event-driven (REC) |
|-----------------|------------------|------------------------|
| Simple | Flexible | Most flexible |
| Hard to extend | Medium complexity | Higher complexity |
| **REC** | Acceptable | Future state |

## 5. Recommendation
Keep chain simple (Approach A) now, add state machine when >10 companies. Jidoka hooks mandatory at cook/test/deploy.

## 6. Handoff to P3
Horizontal dispatch needs: parallel battle groups (alpha/beta/gamma/delta) with dependency graph.
