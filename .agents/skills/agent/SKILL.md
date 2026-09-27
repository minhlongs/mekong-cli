---
name: agent
description: >-
  Domain subagent bridge & management — list, run, info, and dynamically define 25 specialized agents.
---

# /agent — Domain Subagent Bridge & Architecture

The `/agent` skill bridges Google Antigravity to Mekong CLI's 25 domain subagents. It provides direct command execution for `mekong agent` CLI and enables dynamic Antigravity subagent definition.

## CLI Commands

### 1. `mekong agent list`
List all domain agents with descriptions, allowed tools, and delegation paths.
```bash
mekong agent list
mekong agent list --verbose
```

### 2. `mekong agent run <agent> <task>`
Spawn an agent to execute a task and emit structured output.
```bash
mekong agent run cto "Review the architecture of src/harness/pev/"
mekong agent run cfo "Analyze runway and pricing structure" --json
```

### 3. `mekong agent info <agent>`
Inspect detailed agent metadata, allowed tools, and delegation paths.
```bash
mekong agent info cto
```

### 4. `mekong agent assemble "<goal>"`
Dynamically assemble an agent using the NLU + PEV + Memory + Factory pipeline:
```bash
mekong agent assemble "Audit security and vulnerabilities in backend"
```

### 5. `mekong agent create <name>`
Scaffold a new agent definition at `.claude/agents/<name>.md`.
```bash
mekong agent create security-auditor
```

### 6. `mekong agent init <dir>`
Bootstrap an agent project directory from a template.
```bash
mekong agent init ./agents
```

## Antigravity Dynamic Subagent Loading

Antigravity agents can dynamically define and invoke any of the 25 specialized subagents at runtime using `scripts/antigravity_agent_loader.py`.

### Dynamic Loading Workflow:
1. **List all registered subagents**:
   ```bash
   python3 scripts/antigravity_agent_loader.py --list
   ```
2. **Extract `define_subagent` payload**:
   ```bash
   python3 scripts/antigravity_agent_loader.py --get <agent_id>
   ```
3. **Define the subagent in Antigravity**:
   Call Antigravity's `define_subagent` tool with the parameters returned by the loader (`name`, `description`, `system_prompt`, `enable_write_tools`, `enable_subagent_tools`, `enable_mcp_tools`).
4. **Delegate the task**:
   Call Antigravity's `invoke_subagent` with `subagent_name` and the specific goal prompt.

## Registered Domain Subagents (25 Total)

### Executive Leadership & Strategic Counsel (7 Agents)
| ID | Role | Model | Budget | Key Capabilities |
|---|---|---|---|---|
| `sun-tzu` | Advisory Strategist | Pro | 30k | High-stakes strategic counsel, single-turn advisory, risk calculus |
| `ceo` | Chief Executive Officer | Pro | 30k | Final authority, team delegation, override authority (`can_override: true`) |
| `cto` | Chief Technology Officer | Pro | 24k | Code architecture, quality standards, engineering SOP enforcement |
| `cmo` | Chief Marketing Officer | Inherit | 20k | Growth positioning, messaging, multi-channel campaigns |
| `coo` | Chief Operating Officer | Inherit | 16k | Daily operations, workflow logistics, cross-functional execution |
| `cfo` | Chief Financial Officer | Inherit | 16k | Financial models, cash runway, pricing levers, capital purity |
| `cso` | Chief Strategy Officer | Inherit | 16k | Market intelligence, competitive terrain, strategic bets |

### Core Operational & Lifecycle Roles (6 Agents)
| ID | Role | Model | Budget | Key Capabilities |
|---|---|---|---|---|
| `ae` | Account Executive | Inherit | 16k | Client lifecycle, proposals, contracts, revenue onboarding |
| `pm` | Product Manager | Inherit | 20k | Product roadmap, specifications, backlog priorities, feature specs |
| `eng` | Engineer | Inherit | 24k | Code implementation, refactoring, bug fixes, deployment |
| `ops` | Operations & SRE | Inherit | 16k | System monitoring, incident response, vendor & cost tracking |
| `tester` | Quality Assurance | Inherit | 16k | Test suite execution, verification evidence, regression validation |
| `planner` | Tech Lead & Planner | Pro | 20k | Architecture review, dependency graphs, failure-mode analysis |

### Specialized Technical & Task Agents (12 Agents)
| ID | Role | Model | Budget | Definition File |
|---|---|---|---|---|
| `brainstormer` | Ideation & Strategy | Flash | 16k | `.agents/subagents/definitions/brainstormer.md` |
| `code-reviewer` | Code Review | Flash | 16k | `.agents/subagents/definitions/code-reviewer.md` |
| `code-simplifier` | Refactoring & Simplification | Flash | 16k | `.agents/subagents/definitions/code-simplifier.md` |
| `debugger` | Root Cause Analysis | Flash | 16k | `.agents/subagents/definitions/debugger.md` |
| `docs-manager` | Documentation & Specs | Flash | 16k | `.agents/subagents/definitions/docs-manager.md` |
| `fullstack-developer` | Fullstack Implementation | Flash | 16k | `.agents/subagents/definitions/fullstack-developer.md` |
| `git-manager` | Git Operations & Branches | Flash | 16k | `.agents/subagents/definitions/git-manager.md` |
| `journal-writer` | Evolution & Logging | Flash | 16k | `.agents/subagents/definitions/journal-writer.md` |
| `kongming` | Tactical Advisor | Flash | 16k | `.agents/subagents/definitions/kongming.md` |
| `project-manager` | Project Coordination | Flash | 16k | `.agents/subagents/definitions/project-manager.md` |
| `researcher` | Deep Research & Analysis | Flash | 16k | `.agents/subagents/definitions/researcher.md` |
| `ui-ux-designer` | UI/UX & Design Systems | Flash | 16k | `.agents/subagents/definitions/ui-ux-designer.md` |

## Usage

```bash
// turbo
mekong agent $ARGUMENTS
```
