# Project Lifecycle Quick Start

One page. No fluff. Get started.

---

## The Model

```
           PHASES (Where in lifecycle →)
           ┌─────────┬─────────┬─────────┬─────────┬─────────┐
           │ setup   │ core    │ testing │ polish  │ maint.  │
    ┌──────┼─────────┼─────────┼─────────┼─────────┼─────────┤
E   │ Epic │ plan    │ BUILD   │ test    │ ship    │ run     │
P   │  A   │ tasks   │ TASKS   │ tasks   │ tasks   │ tasks   │
I   ├──────┼─────────┼─────────┼─────────┼─────────┼─────────┤
C   │ Epic │ plan    │ BUILD   │ test    │ ship    │ run     │
S   │  B   │ tasks   │ TASKS   │ tasks   │ tasks   │ tasks   │
    └──────┴─────────┴─────────┴─────────┴─────────┴─────────┘
↓ What            → When in project lifecycle
```

**Phases** = Time (where you are)
**Epics** = Features (what you're building)
**Tasks** = Work (how you build it)

---

## Greenfield vs Brownfield

| Aspect | Greenfield | Brownfield |
|--------|------------|------------|
| **Definition** | Empty land | Live building |
| **Freedom** | Maximum | Constrained |
| **Phases** | Linear | Overlapping |
| **Epics** | Capabilities | Changes |
| **Risk** | Over-engineering | Breaking production |

**After first release, everything becomes brownfield.**

---

## Quick Commands

```bash
# Setup
ct init                              # Initialize project
ct phase set setup                   # Set current phase

# Create epic
ct add "EPIC: User Auth" --type epic --phase core --labels "greenfield,capability-auth"

# Create tasks under epic
ct add "Implement login" --parent T001 --phase core
ct add "Write auth tests" --parent T001 --phase testing

# Work
ct focus set T002                    # Focus on task
ct complete T002                     # Mark done
ct next                              # Get suggestion

# Filter
ct list --label greenfield           # By context
ct list --phase core                 # By phase
ct tree T001                         # Epic hierarchy
```

---

## Phase Mapping

| Phase | Lifecycle Stages | What Happens |
|-------|------------------|--------------|
| `setup` | Discovery + Planning | Research, design, scaffold |
| `core` | Build | Implement features |
| `testing` | Test | QA, bug fixes |
| `polish` | Release | Docs, optimization |
| `maintenance` | Operate + Improve | Run, iterate (continuous) |

---

## Epic Patterns

### Greenfield Epic (Capability)

```bash
ct add "EPIC: Payment System" --type epic --labels "greenfield,capability-payments"
# Tasks: Design → Implement → Test → Document
```

### Brownfield Epic (Change)

```bash
ct add "EPIC: Migrate to Stripe" --type epic --labels "brownfield,change-payments,migration"
# Tasks: Analyze → Plan → Implement → Test Rollback → Regression Test → Monitor
```

**Brownfield always includes**: Analysis, Rollback Plan, Regression Tests, Monitoring

---

## Label Conventions

```
Context:     greenfield | brownfield | grayfield
Epic Type:   capability-* | change-* | fix-* | infra-*
Lifecycle:   discovery | planning | build | test | release | operate | improve
Risk:        migration | breaking-change | rollback-required | feature-flag
```

---

## Workflow

```bash
# 1. Start session
ct session start

# 2. Set focus
ct focus set T042

# 3. Work and note progress
ct focus note "Completed auth flow, testing now"

# 4. Complete
ct complete T042

# 5. Next task
ct next

# 6. End session
ct session end
```

---

## Checklist

Before starting:
- [ ] Is this greenfield or brownfield?
- [ ] What phase am I in?
- [ ] Do I have an epic for this work?

For brownfield:
- [ ] Rollback plan?
- [ ] Regression tests?
- [ ] Feature flag?
- [ ] Monitoring task?

---

## One Key Insight

```
Lifecycle never stops.

Discovery → Build → Release → Operate → Improve → Discovery...
     └──────────────────────────────────────────────┘

CI/CD is the engine.
Epics are the steering wheel.
Tasks are the pedals.
```

---

*Full spec: [PROJECT-LIFECYCLE-SPEC.md](./specs/PROJECT-LIFECYCLE-SPEC.md)*
