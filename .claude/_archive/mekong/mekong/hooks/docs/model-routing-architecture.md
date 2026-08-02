# Model Routing Architecture

Two-tier DeepSeek V4 routing system that optimizes cost and capability by directing routine work to Flash (executor) and complex work to Pro (architect).

---

## Tier Overview

| Tier | Model | Role | Traffic Share | Cost/M Tokens | Default? |
|------|-------|------|---------------|---------------|----------|
| Flash | `deepseek-v4-flash` | Executor | 85-95% | ~$0.003 (cached) | Yes |
| Pro | `deepseek-v4-pro[1m]` | Architect | 5-15% | ~$0.14 (cached) | No |

**Flash** handles: file ops, CRUD, boilerplate, unit tests, documentation, formatting, small bug fixes, script execution, linting, git operations.

**Pro** handles: system design, multi-file refactors, framework migrations, architectural decisions, complex debugging, trade-off analysis, performance optimization.

---

## Routing Flow

```
UserPromptSubmit
       |
       v
  [analyze prompt] --counts escalation signals, computes complexity score
       |
       v
  [inject routing guidance] --appends model tier instructions to system prompt
       |
       v
  Flash handles execution (default) --if complexity < threshold
       |
       v
  [on failure] --tracks failure count, auto-escalates on threshold exceeded
       |
       v
  Pro takes over --produces plan or complex implementation
       |
       v
  [after Pro plan] --returns execution to Flash when possible
```

**Key decision points:**
1. **Prompt analysis** happens in `user-prompt-routing.cjs` before the prompt reaches the model.
2. **Routing guidance** is injected into the dynamic suffix of the KV Cache prefix.
3. **Failure feedback** accumulates across subagent calls via session state (`session-state.cjs`), enabling automatic escalation without keyword analysis.

---

## Escalation Signals

Signals are grouped by confidence level, each contributing a weight to the complexity score:

| Level | Weight | Description | Examples |
|-------|--------|-------------|----------|
| Exact | 10 | Unambiguous Pro work | `system design`, `architecture`, `framework migration` |
| Strong | 7 | Probable Pro work | `multi-file refactor`, `performance analysis`, `security review` |
| Pattern | 5 | Structural complexity | `rewrite entire`, `design decision`, `race condition` |
| Weak | 2 | Subtle indicators | `plan`, `strategy`, `think`, `diagram` |
| Failure-based | 7-10 | Programmatic escalation | Repeated failures, unresolved compile errors |

**Scoring:** If total complexity score >= 7 (the `escalationThreshold`), the request routes to Pro. A single exact trigger (10) or strong trigger (7) is enough to escalate alone. Pattern triggers (5) need an additional signal.

Failure-based signals are set programmatically through session state, not matched against keywords. Flash retries cap at 2 consecutive failures before mandatory escalation.

---

## KV Cache Optimization

The system uses a **static prefix + dynamic suffix** strategy to maximize KV Cache hit rates:

- **Static prefix** (pinned, unchanged per session): System instructions, model routing guidance, dev rules, personality prompt. These remain identical across requests so the KV Cache can reuse them.
- **Dynamic suffix** (changes per request): User prompt, agent context, session progress. This trailing content changes each turn without invalidating the cached prefix.

For DeepSeek V4 Flash, cached tokens cost ~$0.003/M vs uncached ~$0.15/M — a 50x cost difference. Maintaining high cache hit rates on the static prefix is the primary cost control mechanism.

---

## Cost Strategy

```
Cost escalation ladder (always try cheaper first):
  Flash (lowest)
    -> Flash + retry (low)
      -> Flash + more context (medium)
        -> Pro (high)
          -> Back to Flash after Pro plan (medium-high)
```

**Rules:**
1. Default to Flash for every request.
2. On failure, retry Flash once (max 2 consecutive failures before escalation).
3. If Flash confidence drops below 30% (`flashConfidenceFloor`), escalate to Pro.
4. After Pro produces a plan, return execution to Flash.
5. Never start on Pro unless explicitly requested or threshold-exceeding signals are detected.

---

## Failure Feedback Loop

Failures are tracked in session state (`session-state.cjs`) across the entire session:

| Signal | Weight | Trigger |
|--------|--------|---------|
| `repeatedFlashFailures` | 10 | Flash fails twice consecutively |
| `unresolvedCompilationErrors` | 10 | Build errors persist after Flash attempts |
| `repeatedTestFailures` | 8 | Tests fail repeatedly under Flash |
| `flashConfidenceBelowThreshold` | 7 | Confidence estimate drops below floor |

Each failure increments a counter in the session state object. On subsequent prompts, the router checks these counters and adds the failure-based signal weights to the complexity score. This ensures the system self-corrects without relying solely on keyword detection.

---

## File Map

| File | Role |
|------|------|
| `user-prompt-routing.cjs` | Analyzes every user prompt, injects model tier routing guidance |
| `session-state.cjs` | Persists session progress, tracks subagent failures across turns |
| `subagent-init.cjs` | Injects context and model routing guidance when spawning subagents |
| `kv-cache-metrics.cjs` | Collects KV cache hit/miss metrics and reports cost savings |
| `lib/model-router-config.cjs` | Central configuration: tiers, escalation signals, thresholds, cost ladder |
| `lib/memory-manager.cjs` | Deterministic repo context caching (loadRepoContext/saveRepoContext) |
| `lib/usage-cost-tracker.cjs` | AI usage cost engine: LiteLLM pricing fetch + JSONL transcript parsing + per-tier cost |

---

## Cost Tracking

Session token usage and cost are tracked via `lib/usage-cost-tracker.cjs` (ported from TAW Terminal).

**Pricing sources:**
1. Live LiteLLM fetch (`model_prices_and_context_window.json`) with 24h disk cache
2. Hardcoded DeepSeek V4 fallback: Flash `$0.003/M`, Pro `$0.14/M`
3. 4-tier fallback: exact → provider prefix → hardcoded → regex heuristic

**Data flow:**
- `session-init.cjs` → writes `os.tmpdir()/ck:usage-cost.json` for statusline
- `user-prompt-routing.cjs` → injects cost summary into routing context
- Per-file mtime+size cache (process lifetime) avoids re-parsing unchanged transcripts

**Output:** `ck-usage-cost.json` contains `{ flash: {tokens, cost}, pro: {tokens, cost}, totalCost, totalTokens }`.

---

## Configuration Reference

All tunable values live in `lib/model-router-config.cjs`:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `escalationThreshold` | 10 | Minimum score to escalate Flash -> Pro |
| `flashConfidenceFloor` | 30% | Below this, route to Pro even without keyword matches |
| `maxFlashRetries` | 2 | Consecutive failures before mandatory escalation |
| `maxFilesForFlash` | 5 | Requests touching more files auto-escalate |
| `maxFlashTokens` | 8000 | Token budget for Flash requests |

---

**Last Updated:** 2026-07-01
