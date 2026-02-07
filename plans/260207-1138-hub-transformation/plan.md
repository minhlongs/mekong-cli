---
title: "Hub Transformation - Mekong CLI Architecture Upgrade"
description: "Restructure packages, implement Plan-Execute-Verify engine, update CLAUDE.md"
status: pending
priority: P1
effort: 16h
branch: master
tags: [architecture, refactor, hub, core-engine]
created: 2026-02-07
---

# Hub Transformation Plan

## Overview

Transform Mekong CLI into a production-grade Hub architecture with:
1. **Monorepo SDK restructure** (`packages/vibe-*`)
2. **Plan-Execute-Verify engine** enhancement (`src/core`)
3. **Documentation updates** (CLAUDE.md with Agent Teams + Binh Phap patterns)

**Priority:** P1 (Critical - Foundation)
**Effort:** 16 hours (4 phases × 4h)
**Status:** Pending

---

## Current State Analysis

### Packages Structure (Flat, No Monorepo)
```
packages/
├── agents/              # Base agents
├── i18n/                # Internationalization
├── newsletter/          # Newsletter module
├── shared/              # Shared utilities
├── ui/                  # UI components
├── vibe/                # Core vibe
├── vibe-agents/         # Agent layer
├── vibe-analytics/      # Analytics (DORA metrics)
├── vibe-bridge/         # Bridge integrations
├── vibe-crm/            # CRM module
├── vibe-dev/            # Dev tools (GitHub sync)
├── vibe-marketing/      # Marketing module
├── vibe-money/          # Payment layer
├── vibe-ops/            # Operations
├── vibe-revenue/        # Revenue tracking
└── vibe-ui/             # UI components
```

**Issues:**
- No unified SDK versioning
- Flat structure = no logical grouping
- No monorepo tooling (lerna/nx/turborepo)
- Duplicate dependencies across packages

### Core Engine (Basic Recipe Executor)
```
src/core/
├── agent_base.py       # Base agent class
├── executor.py         # Shell command executor
├── parser.py           # Markdown recipe parser
└── registry.py         # Recipe discovery
```

**Issues:**
- Executor only runs shell commands (no LLM integration)
- No verification layer
- Missing Plan → Execute → Verify workflow
- No retry/rollback logic

### CLAUDE.md (Missing Modern Patterns)
- No Agent Teams documentation
- Limited Binh Phap integration
- No Hub structure guidance
- Missing ClaudeKit DNA patterns

---

## Phase 1: Monorepo SDK Restructure (4h)

### Objectives
Convert flat packages to structured monorepo with logical grouping.

### New Structure
```
packages/
├── core/                    # Core SDKs
│   ├── vibe/               # Base vibe SDK
│   ├── vibe-agents/        # Agent orchestration
│   └── shared/             # Shared utilities
├── integrations/            # External integrations
│   ├── vibe-bridge/        # Bridge connectors
│   └── vibe-crm/           # CRM integration
├── tooling/                 # Developer tools
│   ├── vibe-dev/           # GitHub sync, DevOps
│   └── vibe-analytics/     # Metrics engine
├── business/                # Business logic
│   ├── vibe-money/         # Payment processing
│   ├── vibe-revenue/       # Revenue tracking
│   ├── vibe-marketing/     # Marketing automation
│   └── vibe-ops/           # Operations
└── ui/                      # UI/UX
    ├── vibe-ui/            # Component library
    ├── ui/                 # Base UI
    └── i18n/               # Localization
```

### Implementation Steps

1. **Create monorepo structure**
   ```bash
   mkdir -p packages/{core,integrations,tooling,business,ui}
   ```

2. **Move packages to categories**
   ```bash
   # Core
   mv packages/vibe packages/core/
   mv packages/vibe-agents packages/core/
   mv packages/shared packages/core/

   # Integrations
   mv packages/vibe-bridge packages/integrations/
   mv packages/vibe-crm packages/integrations/

   # Tooling
   mv packages/vibe-dev packages/tooling/
   mv packages/vibe-analytics packages/tooling/

   # Business
   mv packages/vibe-money packages/business/
   mv packages/vibe-revenue packages/business/
   mv packages/vibe-marketing packages/business/
   mv packages/vibe-ops packages/business/

   # UI
   mv packages/vibe-ui packages/ui/
   mv packages/ui packages/ui/base-ui
   mv packages/i18n packages/ui/
   ```

3. **Setup monorepo tooling**
   - Add `pnpm-workspace.yaml` or `lerna.json`
   - Configure `turbo.json` for build orchestration
   - Update package.json with workspace references

4. **Update package dependencies**
   - Replace hardcoded paths with workspace protocol
   - Example: `"@agencyos/vibe": "workspace:*"`

5. **Create root-level scripts**
   ```json
   {
     "scripts": {
       "build": "turbo run build",
       "test": "turbo run test",
       "dev": "turbo run dev --parallel",
       "lint": "turbo run lint"
     }
   }
   ```

### Success Criteria
- [ ] All packages moved to logical categories
- [ ] Workspace configuration valid
- [ ] Build scripts work across all packages
- [ ] No broken import paths
- [ ] Documentation updated (package locations)

### Risk Assessment
- **High Risk:** Breaking imports in dependent projects
- **Mitigation:** Create symlinks during transition, deprecation notices

---

## Phase 2: Plan-Execute-Verify Engine (6h)

### Objectives
Implement ClaudeKit DNA's Plan-Execute-Verify pattern in `src/core`.

### Architecture Design

```
src/core/
├── __init__.py
├── agent_base.py           # Base agent class (existing)
├── parser.py               # Recipe parser (enhanced)
├── registry.py             # Recipe registry (existing)
├── planner.py              # NEW: Planning layer
├── executor.py             # ENHANCED: LLM-aware executor
├── verifier.py             # NEW: Verification layer
└── orchestrator.py         # NEW: Plan → Execute → Verify flow
```

### Component Specifications

#### 2.1 Planner (`planner.py`)
```python
class RecipePlanner:
    """
    Converts high-level goals into executable task lists.
    Integrates with LLM for decomposition.
    """

    def plan(self, goal: str, context: Dict) -> Recipe:
        """
        Args:
            goal: User's high-level objective
            context: Project context, constraints

        Returns:
            Recipe with steps, dependencies, verification criteria
        """
        # 1. Analyze goal complexity
        # 2. Decompose into atomic tasks
        # 3. Add verification checkpoints
        # 4. Return structured Recipe
```

**Key Features:**
- LLM integration (Claude/Gemini via Antigravity Proxy)
- Task decomposition with dependency graph
- Automatic verification criteria generation

#### 2.2 Enhanced Executor (`executor.py`)
```python
class RecipeExecutor:
    """
    Executes recipe steps with LLM and tool support.
    """

    def execute_step(self, step: RecipeStep) -> ExecutionResult:
        """
        Supports multiple execution modes:
        - Shell commands (existing)
        - LLM tasks (new)
        - API calls (new)
        - File operations (new)
        """
        if step.type == "shell":
            return self._execute_shell(step)
        elif step.type == "llm":
            return self._execute_llm(step)
        elif step.type == "api":
            return self._execute_api(step)
```

**Enhancements:**
- LLM task execution via OpenClaw/Claude
- Retry logic with exponential backoff
- Step rollback on failure
- Progress tracking and logging

#### 2.3 Verifier (`verifier.py`)
```python
class RecipeVerifier:
    """
    Validates execution results against success criteria.
    """

    def verify(self, result: ExecutionResult, criteria: VerificationCriteria) -> VerificationReport:
        """
        Verification types:
        - Command exit codes
        - File existence/content
        - API response validation
        - LLM output quality check
        """
```

**Verification Types:**
- Exit code validation
- File system checks
- Output pattern matching
- LLM-based quality assessment

#### 2.4 Orchestrator (`orchestrator.py`)
```python
class RecipeOrchestrator:
    """
    Coordinates Plan → Execute → Verify workflow.
    """

    def run(self, goal: str) -> OrchestrationResult:
        # PLAN
        recipe = self.planner.plan(goal, context)

        # EXECUTE
        for step in recipe.steps:
            result = self.executor.execute_step(step)

            # VERIFY
            verification = self.verifier.verify(result, step.criteria)

            if not verification.passed:
                # Retry or rollback
                self._handle_failure(step, verification)

        return final_report
```

### Implementation Steps

1. **Create `planner.py`**
   - LLM integration for task decomposition
   - Recipe generation from goals
   - Dependency resolution

2. **Enhance `executor.py`**
   - Add LLM execution mode
   - Implement retry logic
   - Add rollback mechanism

3. **Create `verifier.py`**
   - Define verification criteria schema
   - Implement validators (file, command, LLM)
   - Generate verification reports

4. **Create `orchestrator.py`**
   - Implement Plan → Execute → Verify loop
   - Add failure handling
   - Integrate with existing CLI

5. **Update CLI commands**
   ```bash
   mekong run "implement user authentication"
   # → Plans tasks
   # → Executes with Claude
   # → Verifies results
   ```

### Success Criteria
- [ ] Planner decomposes goals into tasks
- [ ] Executor supports shell + LLM modes
- [ ] Verifier validates results accurately
- [ ] Orchestrator handles full workflow
- [ ] CLI integration working
- [ ] Tests pass (unit + integration)

### Risk Assessment
- **Medium Risk:** LLM API quota exhaustion
- **Mitigation:** Use Antigravity Proxy with fallback models

---

## Phase 3: CLAUDE.md Updates (3h)

### Objectives
Document modern patterns: Agent Teams, Binh Phap, Hub architecture.

### Content Additions

#### 3.1 Agent Teams Section
```markdown
## 第五篇 兵勢 (Bing Shi) - AGENT TEAMS

> "Thế như hoãn huyệt" - Parallel power execution

### Configuration

```bash
# Setting: ~/.claude/settings.json
"CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
```

### Team Workflow

1. Create plan: /plan:hard "task"
2. Execute: "Gọi team thực hiện plan này"
3. CC CLI auto-spawns: FE + BE + Debug + Review
4. Agents sync via Shared Task List

### Mekong CLI Integration

Mekong orchestrator delegates to Agent Teams:
- Planner → Plan generation
- Developer → Implementation
- Tester → Verification
- Reviewer → Code quality
```

#### 3.2 Hub Architecture Section
```markdown
## Hub Architecture (NEW)

### Monorepo Structure

packages/
├── core/           # Foundation SDKs
├── integrations/   # External connectors
├── tooling/        # Developer utilities
├── business/       # Revenue logic
└── ui/             # Interface components

### SDK Dependencies

Core packages (vibe, vibe-agents, shared) are dependencies for all other layers.
Business packages depend on integrations, not vice versa.
```

#### 3.3 Plan-Execute-Verify Section
```markdown
## Core Engine Pattern

Mekong CLI implements ClaudeKit DNA's triadic workflow:

1. **PLAN**: RecipePlanner decomposes goals
2. **EXECUTE**: RecipeExecutor runs tasks (shell/LLM)
3. **VERIFY**: RecipeVerifier validates results

### Usage

```bash
# High-level goal → automatic planning
mekong run "build authentication system"

# Manual recipe execution
mekong cook recipes/deploy-api.md
```
```

#### 3.4 Binh Phap Integration
```markdown
## Binh Phap Quality Gates

Every recipe execution enforces:
- 始計 (Tech Debt): 0 TODOs/FIXMEs before completion
- 作戰 (Type Safety): 0 `any` types
- 謀攻 (Performance): Build < 10s
- 軍形 (Security): 0 high/critical vulnerabilities
- 兵勢 (UX): All async ops have loading states
- 虛實 (Documentation): Updated on completion
```

### Implementation Steps

1. **Read current CLAUDE.md**
2. **Insert new sections** (maintain existing structure)
3. **Update examples** with real Mekong CLI commands
4. **Add cross-references** between sections
5. **Validate Markdown** (no broken links)

### Success Criteria
- [ ] Agent Teams section complete
- [ ] Hub architecture documented
- [ ] Plan-Execute-Verify explained
- [ ] Binh Phap integration clear
- [ ] All code examples tested
- [ ] Markdown valid

---

## Phase 4: Integration & Testing (3h)

### Objectives
Validate all changes work together, fix integration issues.

### Testing Strategy

#### 4.1 Unit Tests
```bash
# Core engine tests
pytest src/core/test_planner.py
pytest src/core/test_executor.py
pytest src/core/test_verifier.py
pytest src/core/test_orchestrator.py

# Package import tests
pytest packages/core/vibe/test_imports.py
pytest packages/tooling/vibe-dev/test_imports.py
```

#### 4.2 Integration Tests
```bash
# Full workflow test
mekong run "create hello world API endpoint"
# → Should plan, execute, verify

# Monorepo build test
cd packages && pnpm run build
# → All packages build successfully

# Agent Teams test
# (Requires CC CLI with AGENT_TEAMS enabled)
```

#### 4.3 Documentation Tests
```bash
# Validate all links in CLAUDE.md
markdown-link-check CLAUDE.md

# Test code examples
./scripts/test-claude-md-examples.sh
```

### Rollback Plan

If critical issues arise:
1. **Git revert** to pre-transformation state
2. **Restore packages** to flat structure (keep backups)
3. **Document blockers** for future attempts

### Success Criteria
- [ ] All unit tests pass
- [ ] Integration tests pass
- [ ] Documentation valid
- [ ] No breaking changes in dependent projects
- [ ] Performance benchmarks met

---

## Unresolved Questions

1. **Monorepo Tool Choice**: Turborepo vs Lerna vs pnpm workspaces?
   - Recommendation: Turborepo (best caching, AgencyOS already uses)

2. **LLM Provider Priority**: Claude vs Gemini for planner?
   - Recommendation: Claude (better planning), Gemini (fallback)

3. **Verification Depth**: How strict should verifier be?
   - Recommendation: Configurable strictness levels

4. **Backward Compatibility**: Support old flat package imports?
   - Recommendation: Yes, via package.json "exports" field for 6 months

5. **Agent Teams Scope**: Should Mekong spawn teams or delegate to CC CLI?
   - Recommendation: Delegate to CC CLI (avoid duplication)

---

## Dependencies

- **Turborepo** (monorepo tooling)
- **Pydantic v2** (enhanced validation)
- **OpenClaw SDK** (LLM integration)
- **Rich** (existing, for console UI)

---

## Risk Summary

| Risk | Severity | Mitigation |
|------|----------|------------|
| Breaking imports | High | Symlinks + deprecation period |
| LLM quota exhaustion | Medium | Antigravity Proxy fallback |
| Test failures | Medium | Comprehensive test suite |
| Documentation drift | Low | Automated link checking |

---

## Next Steps

1. **Review plan** with team/stakeholders
2. **Prioritize phases** (can execute in parallel if needed)
3. **Assign researchers** for Phase 2 (LLM integration patterns)
4. **Create feature branch**: `feature/hub-transformation`
5. **Execute Phase 1** (monorepo restructure)

---

**Total Effort:** 16 hours
**Phases:** 4 (Monorepo 4h + Engine 6h + Docs 3h + Testing 3h)
**Risk Level:** Medium (manageable with proper testing)
**Impact:** High (foundation for all future development)
