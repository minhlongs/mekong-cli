# Roadmap: Deferred Claims → v6.1 Targets

**Created:** 2026-04-17  
**Purpose:** Transparency doc listing claims removed from README.md during pre-launch audit. These are real goals on the roadmap — not abandoned — but not yet evidenced in shipped code as of D-Day 2026-04-21.

---

## Why This Doc Exists

Per a16z solo company doctrine: shipping truth beats vaporware. The README was rewritten to match code reality. Every claim removed here is tracked as a v6.1 target with acceptance criteria.

---

## Deferred Claims → v6.1

### 1. "22 Autonomous Departments"

**Was in README:** "22 autonomous departments — engineering, marketing, sales, finance, legal, compliance, HR"  
**Reality as of 2026-04-17:** 10 layers defined in `factory/contracts/layers.json`. 19 Python agent files in `src/agents/`. 7 departments named in marketing copy.  
**v6.1 Target:** Fully document and ship 22 named departments with working agent entrypoints, runbooks, and demo workflows.  
**Acceptance criteria:**
- `factory/contracts/layers.json` lists 22 layers with descriptions
- Each layer has ≥1 working command with end-to-end test
- `docs/department/` has runbook per department

---

### 2. "385 Pre-built Workflow Templates"

**Was in README:** "385 pre-built workflow templates across 22 departments"  
**Reality:** 443 command definitions (`.claude/commands/*.md`) — these are command specs, not workflow templates. A "workflow template" implies a multi-step DAG recipe with documented inputs/outputs.  
**v6.1 Target:** Tag and publish 50 curated workflow templates (multi-step DAG recipes) with worked examples. Label remainder as "command definitions."  
**Acceptance criteria:**
- `recipes/` directory with ≥50 named workflow YAML files
- Each recipe has: description, steps, expected output, example run
- README accurately calls them "workflow recipes" with verified count

---

### 3. M1/M2 Ultra Performance Benchmarks

**Was in README:** "M1/M2/M3/M4: 7B-14B models | M1 Ultra/M2 Ultra: 32B-70B models"  
**Reality:** Ollama adapter exists (`src/ai/ollama_adapter.py`) but no benchmark scripts or verified load test results in repo.  
**v6.1 Target:** Publish verified benchmarks for Apple Silicon tiers.  
**Acceptance criteria:**
- `scripts/benchmark/run-ollama-benchmark.sh` committed
- Results table in README with model names, tokens/sec, hardware tested
- Tested on M1 Max (owner's machine), M1 Ultra optional

---

### 4. "OpenClaw Runs 24/7 While You Sleep"

**Was in README:** "Autonomous operations engine (OpenClaw) runs 24/7 while you sleep"  
**Reality:** `src/daemon/` scaffolded (heartbeat_scheduler.py, dispatcher.py, jidoka quality gates). Not stress-tested or proven unattended for 24h.  
**v6.1 Target:** Ship daemon with LaunchAgent/systemd unit + 72h stress test report.  
**Acceptance criteria:**
- `mekong/daemon/launchagent.plist` (macOS) or `systemd/mekong-daemon.service` (Linux)
- `docs/daemon-runbook.md` with crash recovery, log rotation, health endpoint
- 72h stress test log committed under `docs/burn-in/`
- README claim updated to include uptime SLA caveat

---

### 5. "5,713 Passing Tests (1,263 TS + 4,450 Python)"

**Was in README:** "5,713 passing (1,263 TS + 4,450 Python)"  
**Reality as of 2026-04-17:** 7,041 Python tests collected; TS vitest failing locally (ESM module error). Actual pass count requires clean CI run.  
**Current status:** Numbers stale — Python count grew to 7,041+, TS count unverified.  
**v6.1 Target:** CI badge with live test count. README updated on every PR.  
**Acceptance criteria:**
- GitHub Actions badge: `Tests: N passing`
- README test count auto-updated via CI script
- Zero test failures on main branch

---

### 6. "542 Skill Definitions" (CLAUDE.md claim)

**Was in CLAUDE.md:** `.claude/skills/ — 542 skill definitions (SKILL.md)`  
**Reality:** 197 `SKILL.md` files in `.claude/skills/`  
**Note:** CLAUDE.md is internal — not in public README — but counts diverge. If global `~/.claude/skills/` files are included, count may be higher. Needs audit.  
**v6.1 Target:** Reconcile count. Either add more skills or correct CLAUDE.md.

---

## Timeline

| Target | Version | Priority |
|--------|---------|----------|
| 22 departments documented | v6.1 | P1 |
| 50 workflow templates in recipes/ | v6.1 | P1 |
| Apple Silicon benchmarks | v6.1 | P2 |
| Daemon 24h stress test + runbook | v6.1 | P1 |
| CI test count badge + auto-update | v6.1 | P1 |
| Skills count reconciliation | v6.2 | P3 |

---

## Reference

- Audit evidence: `docs/claims-audit.md`
- Researcher gap report: `plans/reports/researcher-260417-0804-claims-vs-shipped-gap.md`
- Phase A3 plan: `plans/260417-0832-mekong-cli-deep-unshipped/phase-a3-readme-truthful-rewrite.md`
