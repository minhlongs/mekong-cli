# Brainstorm Report — VentureOS Next Phase

> Phase: post-01 | 2026-07-11T02:5x:xxZ
> Input: `/brainstorm /idea next --plan --deep`
> Author: Claude Code (Anthropic)

## Scout Summary

- **4 compilers**: business-plan, financial-model, mvp-roadmap, pitch-deck — all working, bilingual VN/EN
- **1 workflow**: market-research (5 steps: size, competitors, pricing, demand, gate)
- **2 ventures**: saas-2026-ai-chatbot-platform, startup-2026-test-workflow
- **Zero external deps**, ESM TypeScript, filesystem-as-DB pattern
- **9-phase lifecycle**: IDENTIFY → IDEA → VALIDATE → ARCHITECT → INCORPORATE → SEED → BUILD → SCALE → EXIT
- TODO: The `--deep` flag was requested but not cleared — would add research from web searches and multi-domain analysis. Skipped due to lack of clear next-phase target from user.

## Problem First Inversion

User's question: "What's next for VentureOS?"
Underlying problem: **VentureOS is a working Phase 01 prototype but has no production path forward.** It can run workflows and compile documents, but there's no end-to-end path from IDENTIFY → funded + building.

**Why this matters:**
- The system promises 9 phases; only 1 is implemented in full
- Each new phase needs: inputs from prior phase, workflows to execute it, compilers to synthesize outputs, gate checks
- The empty directories (`knowledge/`, `config/`, `lib/graph/`, `lib/wal/`) suggest planned expansion but no roadmap

## Alternative Problem Framings

| Framing | Implication |
|---|---|
| "What features fill the roadmap fastest?" | Prioritize high-value, low-effort additions |
| "What makes Phase 01→02 transition smooth?" | Focus on IDEA phase workflow + compilers |
| "What's the thin slice that proves the full system?" | One additional phase that demonstrates end-to-end |
| "What's broken in Phase 01 that needs fixing first?" | Address gaps: Chinese compiler not registered, WAL module empty, etc. |

## Evaluated Approaches

### Option A: IDEA Phase Fill-in (Recommended)
**What**: Add Phase 02 (IDEA) workflow + idea-evaluation compiler → closes the first handoff gap
**Pros**: Users can progress ventures from IDENTIFY to IDEA, tests lifecycle continuity
**Cons**: Still only 2 of 9 phases; depth before breadth
**Effort**: 1-2 days |

### Option B: Full Roadmap Sprint (3+ phases parallel)
**What**: Simultaneously build VALIDATE (PMF gate), ARCHITECT (system design), INCORPORATE (legal) phases
**Pros**: Larger surface area coverage, more demo-able
**Cons**: Too many parallel tracks; each phase will be shallow; harder to validate

### Option C: Foundation First (stabilize Phase 01)
**What**: Register chinese-pitch-deck compiler, flesh out lib/wal/, add WAL replay, improve error handling
**Pros**: Reduces technical debt, makes later phases easier to iterate on
**Cons**: Doesn't advance the lifecycle story; feels underwhelming

## Recommended Approach (hybrid: A + C)

**Phase A (1 day):** Register chinese-pitch-deck compiler + WAL foundation (Option C)
**Phase B (2 days):** IDEA phase workflow + idea-validation compiler (Option A)
**Phase C (optional):** VALIDATE phase with PMF gate workflow

### Phase A Details

1. **Register `chinese-pitch-deck` compiler**
   - Create `workflows/compiler/chinese-pitch-deck/compiler.yaml`
   - Add template similar to pitch-deck but Chinese-first
   - Test: `venture compile <id> chinese-pitch-deck`

2. **lib/wal/ module** — WAL compaction + replay
   - `compact()`: merge multiple .jsonl files into one
   - `replay()`: reconstruct venture state from WAL (also replaces `decisions_count` / `events_count` drift)

### Phase B Details

1. **IDEA phase workflow** (`workflows/idea-validation/workflow.yaml`)
   - Step 1: Load decision record + market research
   - Step 2: Generate idea brief (uses new compiler)
   - Step 3: Gate — minimum 2 competitor comparisons, 3 value props

2. **Idea Evaluation Compiler** (`workflows/compiler/idea-brief/compiler.yaml`)
   - Inputs: idea_description, market_trends (from decisions + market-research)
   - Output: `compiled/{id}_idea-brief.md`
   - Template: VSX positioning + 10-slide summary

### Success Metrics

- Chinese pitch deck compiles without error
- New venture can progress phase 01 → 02 end-to-end
- WAL compaction reduces file count without data loss
- All compilers produce non-empty, bilingual output

## Unresolved Questions

1. Should Phase 02 IDEA flow distinguish between "validated idea" vs "rejected idea" — or just ADOPT/ADAPT/ABANDON? (Market research implies validation; IDEA may be redundant)
2. Should WAL replay replace state.json entirely, or stay as a recovery tool only?
3. Should compiler `input.path` glob wildcards be supported for knowledge base queries?
