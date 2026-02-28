# BMad Method Framework Overview

## What is BMad Method?
- **Version installed:** 6.0.0-Beta.7 (installed 2026-02-18)
- **Source:** github.com/bmad-code-org/BMAD-METHOD
- **Core philosophy:** Scale-adaptive AI development — auto-adjusts from bug fix to enterprise
- **Architecture-first:** Epics created AFTER architecture for better quality
- **Anti vibe-coding:** Structured planning eliminates guesswork

## Installation State (mekong-cli)
- **BMM Module (Method):** ✅ Installed — `_bmad/bmm/`
- **BMB Module (Builder):** ✅ Installed — `_bmad/bmb/`
- **Core:** ✅ Installed — `_bmad/core/`
- **Commands:** 55 slash commands in `.claude/commands/bmad-*.md`
- **Config:** `_bmad/bmm/config.yaml` — project=mekong-cli, skill=intermediate
- **Output:** `_bmad-output/` — brainstorming + PRD already generated

## 4 Workflow Phases (Sequential)

### Phase 1: Analysis (`_bmad/bmm/workflows/1-analysis/`)
| Command | Agent | Purpose |
|---------|-------|---------|
| `/bmad-brainstorming` | analyst (Mary) | Expert-guided ideation |
| `/bmad-bmm-market-research` | analyst | Market/competitive analysis |
| `/bmad-bmm-domain-research` | analyst | Domain deep dive |
| `/bmad-bmm-technical-research` | analyst | Tech feasibility |
| `/bmad-bmm-create-product-brief` | analyst | Nail down product idea |

### Phase 2: Planning (`_bmad/bmm/workflows/2-plan-workflows/`)
| Command | Agent | Purpose |
|---------|-------|---------|
| `/bmad-bmm-create-prd` | pm (Sarah) | Product Requirements Doc (REQUIRED) |
| `/bmad-bmm-validate-prd` | pm | PRD validation |
| `/bmad-bmm-edit-prd` | pm | PRD refinement |
| `/bmad-bmm-create-ux-design` | ux-designer | UX planning |

### Phase 3: Solutioning (`_bmad/bmm/workflows/3-solutioning/`)
| Command | Agent | Purpose |
|---------|-------|---------|
| `/bmad-bmm-create-architecture` | architect (Winston) | Tech architecture (REQUIRED) |
| `/bmad-bmm-create-epics-and-stories` | pm | Epics AFTER architecture (REQUIRED) |
| `/bmad-bmm-check-implementation-readiness` | architect | Validation gate (REQUIRED) |

### Phase 4: Implementation (`_bmad/bmm/workflows/4-implementation/`)
| Command | Agent | Purpose |
|---------|-------|---------|
| `/bmad-bmm-sprint-planning` | sm (James) | Sprint plan (REQUIRED) |
| `/bmad-bmm-sprint-status` | sm | Status check |
| `/bmad-bmm-create-story` | sm | Prepare story (REQUIRED) |
| `/bmad-bmm-dev-story` | dev (Alex) | Execute story (REQUIRED) |
| `/bmad-bmm-code-review` | dev | Code review |
| `/bmad-bmm-qa-automate` | qa (Quinn) | Generate tests |
| `/bmad-bmm-retrospective` | sm | Epic retrospective |

## 12+ Specialized Agents

### BMM Agents (9)
| Agent | Name | Role |
|-------|------|------|
| analyst | Mary | Business analysis, research, brainstorming |
| architect | Winston | Technical architecture, readiness check |
| dev | Alex | Story implementation, code review |
| pm | Sarah | PRD, epics/stories, project management |
| qa | Quinn | QA automation, test generation |
| sm | James | Sprint planning, sprint master |
| tech-writer | — | Documentation, diagrams |
| ux-designer | — | UX design workflows |
| quick-flow-solo-dev | — | Fast solo dev for small tasks |

### BMB Agents (3)
| Agent | Role |
|-------|------|
| agent-builder | Create custom agents |
| module-builder | Create custom modules |
| workflow-builder | Create custom workflows |

## Utility Commands (Anytime)
- `/bmad-help` — Context-aware guidance
- `/bmad-party-mode` — Multi-agent collaboration
- `/bmad-bmm-correct-course` — Navigate scope changes
- `/bmad-bmm-document-project` — Auto-document existing project
- `/bmad-bmm-generate-project-context` — Generate LLM-optimized context
- `/bmad-bmm-quick-spec` / `/bmad-bmm-quick-dev` — Quick flow for small tasks
- `/bmad-editorial-review-prose` / `/bmad-editorial-review-structure` — Content review
- `/bmad-review-adversarial-general` — Adversarial review
- `/bmad-shard-doc` — Split large docs
- `/bmad-index-docs` — Index documentation

## Key Insights
1. **Architecture-first** = epics/stories map to real tech decisions, not guesses
2. **Required gates** = PRD → Architecture → Epics → Readiness Check → Sprint
3. **Scale-adaptive** = Quick-flow for small tasks, full flow for enterprise
4. **Agent personas** = each has name, personality, memory for consistent behavior
5. **Config-driven** = `config.yaml` controls language, output paths, skill level
