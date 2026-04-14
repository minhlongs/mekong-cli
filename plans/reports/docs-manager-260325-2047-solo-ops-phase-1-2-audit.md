# Documentation Impact Analysis: Solo Company Operations Phase 1+2

**Date:** 2026-03-25 | **Auditor:** docs-manager | **Status:** MAJOR UPDATES REQUIRED

---

## Executive Summary

Solo Company Operations Phase 1+2 implementation introduces **significant architectural changes** to the daemon/LLM routing layer. The changes are **NOT documented** in current docs, representing a **MAJOR impact** requiring updates to 3+ core documentation files.

**Impact Level:** MAJOR (new subsystem documentation + architecture updates)

---

## Changes Analysis

### 1. Tri-Model LLM Architecture (src/daemon/llm_config.py)

**What Changed:**
- Moved from single/dual-model to **tri-model routing**
- Models now separated by **port/endpoint**:
  - Nemotron 30B (M1 Max :11436) — fast scanner, triage, health checks
  - DeepSeek R1 32B (M1 Max :11435) — deep reasoning, content, sales analysis
  - Qwen 3.5 Plus (DashScope API) — code generation, validation
  - Bailian fallback when local MLX unhealthy

**Current Documentation Status:**
- `docs/codebase-summary.md`: Line 51-54 mentions "3 vars, any provider" but doesn't explain tri-model routing
- `docs/system-architecture.md`: No mention of daemon LLM routing specifics
- `CLAUDE.md`: Lines 68-78 describe "universal endpoint (3 vars)" but outdated

**Files Needing Updates:**
1. `docs/system-architecture.md` — Add daemon LLM routing section
2. `docs/codebase-summary.md` — Update LLM router description with tri-model detail
3. New file needed: `docs/daemon-operations.md` or section in architecture

---

### 2. Heartbeat Scheduler + Loop Config (src/daemon/heartbeat_scheduler.py + .mekong/loops/)

**What Changed:**
- New `HeartbeatScheduler` reads JSON loop configs from `.mekong/loops/`
- Two-tier processing (script check → LLM invocation)
- 5 autonomous loops defined: lead-scan, content-batch, support-triage, sales-ops, monitor
- Config file: `.mekong/heartbeat-config.json` + `.mekong/loops/*.json`

**Current Documentation Status:**
- **No documentation exists** for heartbeat scheduler
- **No documentation exists** for loop configs
- **No documentation exists** for autonomous ops architecture
- `docs/dev-sops.md` doesn't mention daemon startup

**Files Needing Creation/Update:**
1. New: `docs/daemon-operations.md` — Comprehensive daemon operations guide
2. Update: `docs/deployment-guide.md` — Add M1 Max daemon setup section
3. Update: `docs/codebase-summary.md` — Add daemon directory structure

---

### 3. Start-Solo-Ops Script (scripts/start-solo-ops.sh)

**What Changed:**
- New tmux-based launcher for daemon
- Monitors LLM health endpoints in split pane
- Logs to `.mekong/logs/`
- Usage: `bash scripts/start-solo-ops.sh [start|status|stop]`

**Current Documentation Status:**
- **No documentation** for startup script
- **No documentation** for tmux session management
- `docs/dev-sops.md` mentions daemon but not how to launch it

**Files Needing Update:**
1. `docs/dev-sops.md` — Add daemon startup SOP
2. New: `docs/daemon-operations.md` — Quickstart section

---

## Detailed Documentation Requirements

### File 1: `docs/daemon-operations.md` (NEW — ~200 LOC)

**Required Sections:**
- Overview: Solo Company Operations daemon architecture
- LLM Routing: Tri-model architecture (Nemotron/DeepSeek/Qwen)
- Heartbeat Scheduler: Two-tier loop processing
- Configuration: .mekong/heartbeat-config.json + .mekong/loops/*.json
- Startup: `bash scripts/start-solo-ops.sh` usage
- Monitoring: Health checks, logs, tmux session management
- Loop Definitions: lead-scan, content-batch, support-triage, sales-ops, monitor
- Troubleshooting: Common issues, recovery procedures

**References Needed:**
- Link from `docs/system-architecture.md`
- Link from `docs/codebase-summary.md`
- Link from `CLAUDE.md`

---

### File 2: `docs/system-architecture.md` (UPDATE — Add 2-3 sections, ~80 LOC)

**Changes Required:**

1. **Add LLM Routing subsection** under "Agent & Provider System":
   - Explain tri-model routing (Nemotron fast / DeepSeek deep / Qwen API)
   - Show port mapping (11436, 11435)
   - Explain task-to-model routing logic
   - Reference to `src/daemon/llm_config.py`

2. **Add Daemon Architecture subsection** under "Health Monitoring System":
   - Heartbeat scheduler overview
   - Two-tier processing (script + LLM)
   - Loop config structure
   - Event bus integration

3. **Update architecture diagram** (if needed):
   - Add M1 Max local models (11435, 11436)
   - Show DashScope Qwen API as fallback
   - Show .mekong/loops config flow

**Estimate:** 40-50 new lines

---

### File 3: `docs/codebase-summary.md` (UPDATE — ~20-30 LOC)

**Changes Required:**

1. **Update LLM Router description** (line 51-54):
   - Replace "3 vars, any provider" with specific tri-model details
   - Mention Nemotron/DeepSeek/Qwen endpoints

2. **Add Daemon subsection** under Directory Structure:
   ```
   mekong/daemon/                         # Solo Company Operations daemon
   ├── llm_config.py                      # Tri-model routing (Nemotron/DeepSeek/Qwen)
   ├── heartbeat_scheduler.py             # Loop-based task scheduler
   └── loop_definitions.py                # 5 autonomous ops loops
   ```

3. **Add Configuration subsection**:
   - .mekong/heartbeat-config.json
   - .mekong/loops/*.json
   - scripts/start-solo-ops.sh

**Estimate:** 20-25 new lines

---

### File 4: `docs/dev-sops.md` (UPDATE — ~15-20 LOC)

**Changes Required:**

Add new SOP section after "SOP 3: Thêm Agent mới":

**SOP 4: Chạy Solo Company Operations Daemon**
- Prerequisite: LLM models on M1 Max (Nemotron, DeepSeek)
- Start daemon: `bash scripts/start-solo-ops.sh`
- Check status: `bash scripts/start-solo-ops.sh --status`
- View logs: `tail -f .mekong/logs/heartbeat-*.log`
- Stop: `bash scripts/start-solo-ops.sh --stop`

**Estimate:** 15-20 new lines

---

### File 5: `docs/deployment-guide.md` (UPDATE — ~30-40 LOC)

**Changes Required:**

Add M1 Max daemon section after "3. CI/CD Deployment":

**4. M1 Max Local Daemon Deployment**
- Prerequisite: M1 Max with Nemotron/DeepSeek running
- Configuration: Edit `.mekong/heartbeat-config.json`
- Loop configs: Customize `.mekong/loops/*.json`
- Startup: `bash scripts/start-solo-ops.sh`
- Monitoring: Split pane shows LLM health
- Production considerations

**Estimate:** 30-40 new lines

---

## Documentation Coverage Summary

| Doc File | Current Status | Update Type | Est. Lines | Priority |
|----------|----------------|------------|-----------|----------|
| daemon-operations.md | NOT EXISTS | CREATE | 200 | CRITICAL |
| system-architecture.md | INCOMPLETE | UPDATE | +50 | HIGH |
| codebase-summary.md | INCOMPLETE | UPDATE | +25 | HIGH |
| dev-sops.md | INCOMPLETE | UPDATE | +20 | HIGH |
| deployment-guide.md | INCOMPLETE | UPDATE | +35 | MEDIUM |

**Total New Documentation:** ~330 LOC

---

## Impact Statement

**Docs Impact: MAJOR**

### Rationale:
1. **New Subsystem:** Daemon/heartbeat scheduler completely undocumented
2. **Architecture Change:** LLM routing now tri-model (previously abstract)
3. **Configuration:** New JSON config files (.mekong/heartbeat-config.json, .mekong/loops/)
4. **Operations:** New startup script and management procedures
5. **Cross-Cutting:** Changes affect system-architecture, codebase understanding, deployment, and SOPs

### Risk if Not Updated:
- Developers unable to understand daemon architecture
- Unclear how LLM routing works (which model for what task)
- No guidance on heartbeat scheduler configuration
- Missing startup/monitoring procedures
- Operational knowledge lost if not documented

---

## Verification Checklist

After updates, verify:
- [ ] daemon-operations.md exists with all 8 sections
- [ ] system-architecture.md mentions LLM routing AND daemon subsystem
- [ ] codebase-summary.md shows .mekong/daemon structure
- [ ] dev-sops.md has SOP 4 with start-solo-ops.sh examples
- [ ] deployment-guide.md has M1 Max section with .mekong config details
- [ ] All internal links consistent (.md cross-references work)
- [ ] Code examples reference actual file paths in repo
- [ ] Config examples reference actual .mekong/*.json files

---

## Notes

- All changes reference actual implementation in Phase 1+2 code
- No breaking changes to existing architecture — daemon is additive
- Tri-model routing is NOT breaking (still uses standard LLM client interface)
- Heartbeat scheduler is optional (daemon mode, not required for CLI)

---

_Assessment complete. Ready for documentation implementation._
