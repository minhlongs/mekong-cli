# Phần 3: Horizontal Dispatch — Battle Groups (Parallel Execution)

> Status: DRAFT

## 1. Brainstorm Contract (reuse P1)
Outcome: Parallel battle group dispatch plan with dependency graph and merge strategy.
Constraints: (1) Groups run concurrently when deps satisfied (2) Merge outputs deterministically (3) Failure in one group does NOT block independent groups
Non-goals: (1) No dynamic group creation (static 4 groups) (2) No cross-group data sharing during execution
Acceptance: Dependency DAG + merge_output_key contract + failure isolation spec

## 2. Current State (topology.py)
DEFAULT_BATTLE_GROUPS:
  alpha: [swot, audit, venture:terrain] -> intelligence_brief
  beta:  [plan, competitive]             -> strategy_brief (depends: alpha)
  gamma: [cook, marketing, sprint]       -> delivery_package (depends: beta)
  delta: [launch, deploy, audit]         -> campaign_result (depends: gamma)

Pain points:
- Groups are hardcoded dict, not configurable per company
- No merge strategy defined (just list concatenation)
- audit appears in alpha AND delta (duplicate execution risk)
- No timeout per group

## 3. Proposed Architecture

### 3.1 Dependency DAG
```
  alpha (no deps)
    |
    v
  beta (depends: alpha)
    |
    v
  gamma (depends: beta)
    |
    v
  delta (depends: gamma)
```

### 3.2 Group Execution Model
```
dispatcher.get_ready_groups()
    -> [alpha]  # only alpha ready (no deps)
    -> start_group("alpha")
    -> execute_parallel(alpha.commands)
    -> collect results -> complete_group("alpha", results)
    -> loop: now beta ready
```

### 3.3 Merge Strategy
| group | merge_output_key | format | merge_fn |
|-------|-----------------|--------|----------|
| alpha | intelligence_brief | JSON | {swot: {}, audit: {}} |
| beta | strategy_brief | JSON | {plan: {}, competitive: {}} |
| gamma | delivery_package | JSON | {cook: {}, marketing: {}} |
| delta | campaign_result | JSON | {launch: {}, deploy: {}} |

Merge = structured dict, NOT list concatenation.

## 4. Trade-off
| A: Hardcoded groups | B: Per-company config | C: Dynamic AI-generated (REC) |
|--------------------|-----------------------|-------------------------------|
| Fast to implement | Flexible | Most flexible |
| No customization | YAML per company | AI decides groups |
| **REC now** | Next phase | Future state |

## 5. Recommendation
Keep hardcoded groups (A) for now. Add YAML config in Phase 2 when >5 companies use different strategies.
CRITICAL: deduplicate audit command (appears twice) -> execute once, reference in both alpha and delta.

## 6. Handoff to P4
Diagonal loop needs: MRR tracking, cycle learning, auto_dispatch flag.
