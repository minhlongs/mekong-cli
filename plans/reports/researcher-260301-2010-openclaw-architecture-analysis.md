# OpenClaw Architecture Analysis — Tôm Hùm Autonomous Daemon v2026.2.27

## Executive Summary

**Tôm Hùm (OpenClaw Worker)** is a sophisticated autonomous daemon orchestrating CC CLI (Claude Code) across multiple projects. Core architecture separates concerns into modular sub-systems via **Facade Pattern** — backward-compatible API shielding 14+ focused modules. Mission lifecycle: **file-based IPC** (watch `tasks/` dir) → **priority queue** → **complexity classifier** → **brain executor** → **post-mission gate** → **self-learning loop**. Designed for 24/7 production autonomy with thermal protection, dead-letter queues, and AGI-level self-correction.

---

## DNA: What's Worth Keeping (Open-Source AGI Framework)

### 1. **Three-Phase Autonomous Cycle (始計→謀攻→軍形)**
**Pattern:** Scan → Plan → Verify (repeats per project)

**Open-Source Value:** YAGNI-compliant QA framework — no fake fixes.
- **Phase 1 (始計 Scan):** `npm run build && npm run lint && npm test` — detect REAL issues
- **Phase 2 (謀攻 Plan):** Classify severity, generate targeted `/cook` missions, dedup recent fixes
- **Phase 3 (軍形 Verify):** Re-scan, GREEN→advance to next project, RED→retry max 3 cycles
- **Lesson:** Prevents "fix spam" — only dispatches actionable issues

**Decoupling:** `auto-cto-pilot.js` is pure logic, zero dependency on Antigravity/Telegram infrastructure.

### 2. **Mission Complexity Classifier**
**Pattern:** Auto-route based on keyword detection + intent heuristics

**Open-Source Value:** Teachable routing for multi-model workflows.
- Classifies: `simple` (15min) | `medium` (30min) | `complex` (60min) | `strategic` (90min)
- Keyword detection: "refactor", "redesign", "architecture" → complex
- Timeout enforcement prevents hung missions
- **Reusable:** Post-process classifier output to route to different models (Sonnet vs Opus vs local)

**Code:** `mission-complexity-classifier.js` (under 200 lines, stateless)

### 3. **Dead Letter Queue (DLQ) + Write-Ahead Log (WAL)**
**Pattern:** Resilient task persistence across crashes

**Open-Source Value:** Production-grade reliability for task queues.
- Failed missions (3+ retries) → `tasks/dead-letter/` for manual review
- WAL in `.openclaw/` survives daemon restart
- Mission metadata: retry count, error reason, timestamp
- **Lesson:** Prevents silent task loss — every failure is auditable

**Code:** `task-queue.js` (initDLQ, moveToDeadLetter, archiveProcessedMissions)

### 4. **Self-Learning Loop (Post-Mission Gate + Journal)**
**Pattern:** Record→Reflect→Improve

**Open-Source Value:** Foundational AGI Level 3-5 pattern.
- **AGI L3 Gate:** Post-mission build verification + auto-commit
- **AGI L5 Journal:** Record success/failure/duration in `data/mission-history.json`
- **Learning Engine:** Analyze patterns, suggest timeouts, detect blockers
- **Evolution Engine:** Generate self-correction tasks every 2h

**Decoupling:** Journal format (timestamp, success, tokens, build result) is model-agnostic — works with any executor.

---

## What's Personal Infrastructure (Remove for Open Source)

### 1. **Antigravity Proxy Integration** (Port 9191)
**Why it's tightly coupled:**
- Hardcoded in `config.js`: `PROXY_PORT: 20129`, `CLOUD_BRAIN_URL: http://127.0.0.1:20128`
- `mission-dispatcher.js` checks `isProAvailable()` to route deep tasks to Pro pane
- Model fallback chain hardcoded: `['claude-sonnet-4-6', ..., 'gemini-3-pro']`
- Telegram/Google Ultra integration assumes Antigravity auth

**Generalization:** Replace with **abstract provider interface:**
```js
// Instead of: ANTHROPIC_BASE_URL hardcoded
class LLMProvider {
  async runMission(prompt, timeout, model) { /* abstract */ }
  isAvailable() { /* abstract */ }
  fallbackModel() { /* abstract */ }
}
```

### 2. **Multi-Tmux Pane Architecture (Dual-Stream Flywheel)**
**Why it's personal:**
- Assumes 2 panes (P0=Claude Pro, P1=Gemini API) in single tmux session
- `brain-process-manager.js` captures pane output via `tmux capture-pane -t tom_hum:brain.${pIdx}`
- LLM Vision (`llm-interpreter.js`) reads P1 pane to detect "busy" state before dispatching
- Auto-CTO skips dispatch if P1 is in "question" loop (3+ consecutive)

**Generalization:** Model-agnostic **process pool:**
```js
class BrainPool {
  constructor(size) { this.workers = []; }
  async runMission(mission) {
    return this.workers[this.nextIdx()].run(mission);
  }
}
```

### 3. **Project-Specific Routing & Revenue Health**
**Why it's personal:**
- `detectProjectDir()` has hardcoded routes: `'well'→'apps/well'`, `'84tea'→'apps/84tea'`
- `auto-cto-pilot.js` generates project-specific "Open Source RaaS" missions
- `revenue-health-scanner.js` monitors payment system (PayOS/Polar) health
- `clawwork-integration.js` tracks GDP-Value economic metrics

**Generalization:** Move routing to config file, make revenue scanner optional.

### 4. **Binh Pháp Framework Hardcoding**
**Why it's personal:**
- `config.BINH_PHAP_TASKS[]` lists 14 pre-defined tasks (console_cleanup, type_safety, a11y_audit)
- `buildPrompt()` injects Binh Pháp chapters into prompts (e.g., "始計 DEEP SCAN")
- `/bmad` commands hardcoded in routing logic
- Assumes Vietnamese language for prompts

**Generalization:** Task templates should be YAML/JSON-driven, language-agnostic.

---

## Generalization: AGI Task Orchestration Framework (Reusable)

### Minimal Core for Open Source:

```
openclaw-core/
├── config-schema.json          # Project routes, complexity keywords, task templates
├── task-queue/
│   ├── queue.js                # FIFO + priority sorting + DLQ
│   ├── journal.js              # Mission telemetry
│   └── wal.js                  # Write-ahead log recovery
├── mission/
│   ├── classifier.js           # Complexity detection (stateless, configurable)
│   ├── dispatcher.js           # Routing + prompt building
│   └── executor.js             # Abstract LLM provider interface
├── autonomy/
│   ├── scanner.js              # Project health scanning (build/lint/test)
│   ├── auto-planner.js         # Generate missions from issues
│   └── post-gate.js            # Verification + auto-commit
└── observability/
    ├── health-server.js        # /health, /metrics endpoints
    ├── mission-journal.js       # Telemetry + learning
    └── thermal-monitor.js       # System load tracking (optional)
```

### Configuration Injection Points:

```yaml
# openclaw-config.yaml
projects:
  - name: myproject
    path: ./apps/myproject
    scripts: [build, lint, test]

complexity_keywords:
  simple: ["add", "update"]
  complex: ["refactor", "redesign", "architecture"]

task_templates:
  build_fix: |
    Fix build error in {file}: {code} {message}.
    Run npm run build after fixing.
  type_safety: |
    Audit TypeScript any types — report all locations, fix them.

providers:
  - type: anthropic
    model: claude-sonnet-4-6
    base_url: https://api.anthropic.com
```

---

## Vibe Coding Factory Flow (Emerging Pattern)

**Found in:** `vibe-factory-monitor.js` (referenced but not in core files)

**Concept:** Idle pane task injection during off-peak times.

**Open-Source Pattern:**
1. Detect idle executor (no active mission)
2. Pop next task from queue
3. Inject with adaptive delays (respects load)
4. Record metrics (success, duration, tokens)
5. Feed to learning engine for next round

**Reusable:** Task batching strategy for serverless/distributed executors.

---

## Mission Dispatch Lifecycle (End-to-End)

```
File Detection (fs.watch + 5s poll)
  ↓
Priority Sort (CRITICAL > HIGH > MEDIUM > LOW > unmarked)
  ↓
Complexity Classification (simple/medium/complex/strategic)
  ↓
Project Routing (keyword match → git dir)
  ↓
Prompt Building (task + mandate + context + plan linking)
  ↓
Brain Executor (claude -p OR tmux pane)
  ↓
Thermal Gate (pause if load > 80 OR RAM < 30MB)
  ↓
Mission Journal (record: duration, tokens, success)
  ↓
Post-Mission Gate (build verification + auto-commit)
  ↓
Learning Reflection (analyze failure, suggest retry strategy)
  ↓
Archive to tasks/processed/ OR tasks/dead-letter/
```

**Key Contract:** Mission file → JSON metadata → executor receives string prompt, returns `{success, result, elapsed, failureType}`

---

## Thermal Protection (M1-Specific, Generalizable)

**Found in:** `m1-cooling-daemon.js`

**Pattern:** Load velocity + resource tracking → proactive dispatch pause

**Thresholds (M1-tuned, configurable):**
- OVERHEAT: load > 80 OR RAM < 30MB → pause
- SAFE: load < 50 AND RAM > 100MB → resume
- Hysteresis prevents oscillation

**Open-Source Value:** Template for CPU/memory-constrained environments.

**Generalizable:**
- Replace sysctl calls with `/proc/loadavg` on Linux
- Swap tracking: `vm.swapusage` → `/proc/swaps`
- Thermal warning: `pmset` → `/sys/class/thermal/` on Linux

---

## Key Insights for AGI Framework Design

1. **Stateless Classifiers:** Complexity detection, intent routing, error classification all pure functions — no hidden state
2. **File-Based IPC:** Mission discovery via filesystem (not AMQP/Redis) — simpler, no external dependencies
3. **Observability First:** Journal every mission, post-gate every build, thermal monitor every 90s
4. **Self-Healing:** WAL recovery, DLQ triage, thermal intervention — no silent failures
5. **Learning Loop:** Post-mortem analysis feeds back into timeout/strategy suggestions
6. **Modular Facade:** 56KB monolith refactored into 14 sub-modules, backward-compatible API

---

## Unresolved Questions

1. How does the learning engine train on mission patterns without full solution traces (only success/fail)?
   - Current: `learning-engine.js` heuristics (duration vs complexity, error keywords)
   - Needed: Full reasoning trace capture for meta-learning

2. Is AGI Level 6+ (Self-Evolving Engine) actually reaching autonomous code generation, or just task routing?
   - Appears to be task generation only (creating new missions, not fixing code directly)

3. How are multi-project dependencies handled (e.g., shared package.json, monorepo linking)?
   - Current: Per-project scanning independent (no cross-project analysis)

4. What's the recovery story for when the learning engine itself generates bad tasks?
   - Safeguard: `mission_dedup_ttl` prevents re-dispatch, but what if task is legitimately bad?

5. How does thermal gating interact with strategic missions (90min timeout)? Will they always timeout on loaded M1?

---

## Recommendations for Open-Source Release

1. **Extract Core:** Keep `task-queue`, `complexity-classifier`, `post-mission-gate`, `thermal-monitor`
2. **Generalize:** Replace Antigravity with abstract provider, remove project-specific routing
3. **Document:** YAML config schema, telemetry format, provider interface contract
4. **Simplify:** Drop Binh Pháp hardcoding, make task templates configurable
5. **Test:** Unit tests for classifier, queue, journal — min 80% coverage
6. **Reference:** Include working example config for single project + 3 tasks

**Target Ecosystem:** Multi-model LLM orchestration framework for continuous autonomy on consumer hardware.

