# Tool Execution Trace Report

**Project:** Mekong CLI v6.0  
**Work Context:** /Users/macbook/mekong-cli  
**Report Path:** /Users/macbook/mekong-cli/plans/reports/step7-tool-execution-trace.md

---

## 1. Tool Registry Architecture

### File: `/Users/macbook/mekong-cli/src/core/tool_registry.py` (532 lines)

#### Key Classes & Data Structures

| Class/Enum | Purpose | Lines |
|------------|---------|-------|
| `ToolType` (Enum) | Tool categories: BUILTIN, CUSTOM, API, MCP, SHELL | 24-33 |
| `ToolParameter` | Parameter schema: name, type, description, required, default | 35-50 |
| `Tool` | Core tool dataclass with execution metadata | 52-72 |
| `ToolRegistry` | Main registry for registration, lookup, execution | 88-576 |

#### Registration Flow

```python
# ToolRegistry.register() - src/core/tool_registry.py:102-160
def register(
    self,
    name: str,
    description: str,
    tool_type: ToolType = ToolType.CUSTOM,
    parameters: Optional[List[ToolParameter]] = None,
    command_template: str = "",
    handler: Optional[Callable[..., Any]] = None,
    tags: Optional[List[str]] = None,
) -> Tool:
```

**Registration Sources:**
1. **Manual** - `register()` API for Python functions
2. **CLI Discovery** - `discover_from_cli(command)` parses `--help` output (line 294)
3. **OpenAPI Specs** - `discover_from_openapi(spec, base_url)` auto-generates tools (line 355)
4. **MCP Servers** - `connect_mcp_server(url)` for MCP protocol tools (line 415)

#### Execution Flow

```python
# ToolRegistry.execute() - src/core/tool_registry.py:201-292
def execute(self, name: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    # 1. Lookup tool
    tool = self._tools.get(name)
    if not tool: raise ValueError(f"Tool not found: {name}")
    
    # 2. Validate params against schema
    # 3. Route to handler:
    #    - handler (Python function) if provided
    #    - command_template (shell) with sanitization
    #    - API endpoint for ToolType.API
    #    - MCP client for ToolType.MCP
    
    # 4. Update metrics (success_count, failure_count, last_used)
    # 5. Persist registry state
    return {"success": bool, "output": str, "duration_ms": int}
```

#### Built-in Tools (registered at init)

```python
# _register_builtins() - lines 99-100
- shell:run          # Shell command execution
- file:read          # File read
- file:write         # File write
- file:list          # Directory listing
- file:delete        # File deletion
- api:request        # HTTP API requests
- mcp:call           # MCP server calls
```

#### Security Integration

```python
# Shell execution uses CommandSanitizer (lines 249-268)
from src.core.command_sanitizer import CommandSanitizer
sanitizer = CommandSanitizer()
sanitized = sanitizer.sanitize(command_template.format(**params))
# Fail-closed: if sanitizer missing, shell:run blocked
```

#### Persistence

- **Path:** `.mekong/tool_registry.yaml` (configurable)
- **Format:** YAML with tool metadata + metrics
- **Auto-save:** On every registration/execution (lines 286, 315)

---

## 2. Permission Registry Architecture

### File: `/Users/macbook/mekong-cli/src/core/tool_permission_registry.py` (135 lines)

#### Key Classes & Enums

| Class/Enum | Purpose | Lines |
|------------|---------|-------|
| `ToolRisk` (Enum) | READ_ONLY, WRITE, EXECUTE, DESTRUCTIVE | 19-24 |
| `PermissionMode` (Enum) | DEFAULT, PLAN, BYPASS, ACCEPT_EDITS | 26-31 |
| `ToolSpec` | Tool name, risk, description, allowed_agents | 33-47 |
| `ToolPermissionRegistry` | Permission management per agent | 51-134 |

#### Permission Check Logic

```python
# check_permission() - src/core/tool_permission_registry.py:90-118
def check_permission(self, tool_name: str, agent_name: str = "*") -> bool:
    tool = self._tools.get(tool_name)
    if not tool: return False
    
    # Agent allowlist
    if "*" not in tool.allowed_agents and agent_name not in tool.allowed_agents:
        return False
    
    # Mode-based restrictions
    if self.mode == PermissionMode.PLAN:
        return tool.risk == ToolRisk.READ_ONLY
    
    if self.mode == PermissionMode.BYPASS:
        return True
    
    if self.mode == PermissionMode.ACCEPT_EDITS:
        return tool.risk in (ToolRisk.READ_ONLY, ToolRisk.WRITE)
    
    # DEFAULT mode
    return tool.risk in (ToolRisk.READ_ONLY, ToolRisk.WRITE)
```

#### Default Tool Specs (registered at init)

```python
# _register_defaults() - lines 59-88
READ_ONLY: file_read, file_search, grep, task_list, git_status, api_get
WRITE: file_write, file_edit, git_commit, api_post
EXECUTE: shell_run, python_run, npm_run, docker_run
DESTRUCTIVE: file_delete, git_reset_hard, docker_rm, system_reboot
```

#### Integration Points

- **Agent filtering:** `get_allowed_tools(agent_name="*")` returns permitted tools
- **Mode switching:** `set_mode(PermissionMode)` changes global behavior
- **Audit trail:** Integrates with Governance layer (mentioned in docstring)

---

## 3. Verification Pipeline (PEV Verifier)

### File: `/Users/macbook/mekong-cli/src/harness/pev/verifier.py` (484 lines)

#### Key Classes

| Class | Purpose | Lines |
|-------|---------|-------|
| `VerificationStatus` | PASSED, FAILED, WARNING | 20-23 |
| `VerificationCheck` | Individual check result | 34-40 |
| `VerificationReport` | Aggregated report with summary | 53-68 |
| `RecipeVerifier` | Main verification engine | 71-481 |

#### Verification Pipeline

```python
# RecipeVerifier.verify() - src/harness/pev/verifier.py:83-481
def verify(self, result: ExecutionResult, criteria: VerificationCriteria, 
           strict_mode: bool = False) -> VerificationReport:
    # 1. Exit code check (must be 0 for success)
    # 2. Output contains patterns (regex + substring)
    # 3. Output NOT contains forbidden patterns
    # 4. File existence checks
    # 5. File content pattern matching
    # 6. JSON output validation (if verify_json_command provided)
    # 7. Custom command checks (run verification commands)
    # 8. TODO list completion
    # 9. Log pattern checks
    # 10. TypeScript :any checks (ruff)
    # 11. Security vulnerability scan (bun audit)
    # 12. Aggregate → report.passed = all PASSED (warnings OK unless strict)
```

#### Verification Criteria Structure

```python
# VerificationCriteria dataclass - lines 25-33
@dataclass
class VerificationCriteria:
    expected_exit_code: int = 0
    output_contains: List[str] = field(default_factory=list)      # regex patterns
    output_not_contains: List[str] = field(default_factory=list)  # forbidden
    file_exists: List[str] = field(default_factory=list)
    file_contains: Dict[str, str] = field(default_factory=dict)   # file -> pattern
    verify_json_command: str = ""                                 # cmd returning JSON
    todo_file: str = ""                                           # path to TODO file
    log_contains: List[str] = field(default_factory=list)
    log_not_contains: List[str] = field(default_factory=list)
    no_any_types: bool = False
    no_security_vulns: bool = False
    custom_checks: List[Dict] = field(default_factory=list)
```

---

## 4. Recipe System Map

### Parser: `/Users/macbook/mekong-cli/src/harness/pev/parser.py` (431 lines)

#### Recipe Format (Markdown with Frontmatter)

```markdown
---
id: recipe-id              # slug
name: "Readable Name"      # human title
intent: deploy             # NLU intent tag
model: claude-sonnet-4     # override default engine model
temperature: 0.2           # override default temperature
retries: 3                 # per-step retry count
---

# Goal Heading

Description text...

## Steps

1. **Step Title** — Step description
   Command: `shell command`
   
2. **Another Step** — Description
   Command: `another command`

## Verification

- Expected output patterns
- File existence checks
- etc.
```

#### Parsing Pipeline

```python
# RecipeParser.parse() - src/harness/pev/parser.py:68-160
def parse(self, markdown: str) -> Recipe:
    # 1. Extract YAML frontmatter (--- ... ---)
    # 2. Parse body sections by ## headings
    # 3. Parse steps from ## Steps section (numbered list with **Title** — desc)
    # 4. Parse verification from ## Verification section (bullet list)
    # 5. Build Recipe dataclass with steps, criteria, metadata
```

#### Recipe Data Structures

```python
# Recipe - lines 10-22
@dataclass
class Recipe:
    id: str
    name: str
    intent: str
    description: str
    steps: List[RecipeStep]
    verification: VerificationCriteria
    metadata: Dict[str, Any]

# RecipeStep - lines 24-33
@dataclass
class RecipeStep:
    order: int
    title: str
    description: str
    command: str = ""
    params: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[int] = field(default_factory=list)
```

#### Token Generation (for LLM context)

```python
# to_prompt_tokens() - lines 162-427
# Generates PromptToken list with roles:
# SYSTEM, USER, ASSISTANT, EXAMPLE, CONTEXT, VERIFICATION
# Used by RecipePlanner for LLM planning
```

### Recipe Directory Structure

```
/Users/macbook/mekong-cli/
├── src/harness/pev/recipes/
│   ├── __init__.py
│   ├── __template__.md
│   └── hello-world.md
├── recipes/
│   └── cloudflare/ (configure-r2-storage.md, deploy-workers.md, setup-cloudflare.md)
└── .archive/top-level/recipes/ (legacy recipes)
```

---

## 5. Tool Execution Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         MEKONG CLI TOOL EXECUTION FLOW                       │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────────┐     ┌──────────────────┐     ┌────────────────────────────┐
│  USER/AGENT  │────▶│  COMMAND ENTRY   │────▶│  PERMISSION CHECK          │
│  (CLI/Bot)   │     │  (cook command)  │     │  ToolPermissionRegistry    │
└──────────────┘     └──────────────────┘     └──────────────┬─────────────┘
                                                              │
                          ┌───────────────────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           RECIPE ORCHESTRATOR                                │
│  src/core/orchestrator/runner.py:RecipeOrchestrator                         │
│                                                                              │
│  1. PLAN   ──▶ RecipePlanner (src/harness/pev/planner.py)                  │
│     - LLM decomposes goal → Recipe                                          │
│     - Validates DAG (dependencies, cycles)                                  │
│                                                                              │
│  2. EXECUTE ──▶ RecipeExecutor (src/harness/pev/executor.py)               │
│     - Iterates steps in order (or DAG parallel)                             │
│     - Executes via step.type:                                               │
│       • shell  ──▶ subprocess (with retry, circuit breaker)                 │
│       • llm    ──▶ LLMClient completion                                     │
│       • api    ──▶ HTTP request                                             │
│       • browse ──▶ Playwright browser                                       │
│       • tool   ──▶ ToolRegistry.execute() ◀── KEY INTEGRATION               │
│                                                                              │
│  3. VERIFY  ──▶ RecipeVerifier (src/harness/pev/verifier.py)               │
│     - Checks exit code, output patterns, files, JSON, custom                │
│     - Returns VerificationReport (passed/failed + checks)                   │
└─────────────────────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            TOOL REGISTRY                                     │
│  src/core/tool_registry.py:ToolRegistry                                     │
│                                                                              │
│  execute(name, params)                                                      │
│    │                                                                        │
│    ├─▶ Built-in handler (Python function)                                   │
│    ├─▶ Shell command ──▶ CommandSanitizer.sanitize() ──▶ subprocess        │
│    ├─▶ API endpoint ──▶ HTTP request                                        │
│    ├─▶ MCP server ──▶ MCP protocol call                                     │
│    └─▶ Custom handler (registered Python callable)                          │
│                                                                              │
│  Updates metrics: success_count, failure_count, last_used                  │
│  Persists to .mekong/tool_registry.yaml                                     │
└─────────────────────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         VERIFICATION RESULT                                  │
│  - OrchestrationResult (status, failed_steps, errors)                       │
│  - StepResult (verification: VerificationReport)                            │
│  - Rollback triggered on failure if enabled                                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Key Entry Points (File:Line References)

| Component | File | Line | Description |
|-----------|------|------|-------------|
| **CLI Entry** | `src/cli/cook_command.py` | 108 | `cook_auto` command (typer) |
| **CLI Entry (legacy)** | `src/commands/core_commands.py` | 46 | `cook` function |
| **Orchestrator** | `src/core/orchestrator/runner.py` | 88 | `RecipeOrchestrator.__init__` |
| **Orchestrator.run()** | `src/core/orchestrator/runner.py` | 139 | `run_from_goal()` / `run_recipe()` |
| **Planner** | `src/harness/pev/planner.py` | 393 | `RecipePlanner.decompose_goal()` |
| **Executor** | `src/harness/pev/executor.py` | 86 | `RecipeExecutor.execute_step()` |
| **Executor._execute_shell_step()** | `src/harness/pev/executor.py` | 626 | Shell execution with retry |
| **Verifier** | `src/harness/pev/verifier.py` | 83 | `RecipeVerifier.verify()` |
| **ToolRegistry.register()** | `src/core/tool_registry.py` | 102 | Manual tool registration |
| **ToolRegistry.execute()** | `src/core/tool_registry.py` | 201 | Tool execution entry |
| **ToolRegistry.discover_from_cli()** | `src/core/tool_registry.py` | 294 | CLI auto-discovery |
| **ToolRegistry.discover_from_openapi()** | `src/core/tool_registry.py` | 355 | OpenAPI auto-discovery |
| **Permission.check_permission()** | `src/core/tool_permission_registry.py` | 90 | Permission gate |
| **CommandSanitizer.sanitize()** | `src/core/command_sanitizer.py` | 50 | Shell security filter |
| **RecipeParser.parse()** | `src/harness/pev/parser.py` | 68 | Markdown → Recipe |
| **RecipeParser.to_prompt_tokens()** | `src/harness/pev/parser.py` | 162 | Recipe → LLM tokens |

---

## 7. Integration Points Summary

### ToolRegistry ↔ PermissionRegistry
- ToolRegistry stores `Tool` objects with metadata
- PermissionRegistry stores `ToolSpec` with risk/agents
- No direct coupling - orchestration layer coordinates both

### RecipeExecutor ↔ ToolRegistry
- Step type `tool` calls `ToolRegistry.execute(name, params)`
- Other step types (shell, llm, api, browse) execute directly
- ToolRegistry handles its own sanitization for shell commands

### RecipeVerifier ↔ ExecutionResult
- Receives `ExecutionResult` from executor
- Runs all verification criteria
- Returns `VerificationReport` for orchestrator decision

### RecipeParser ↔ RecipePlanner
- Parser produces `Recipe` with `VerificationCriteria`
- Planner uses `to_prompt_tokens()` for LLM context
- Planner can re-plan failed branches (replan_failed_branch)

---

## 8. Security Architecture

1. **CommandSanitizer** (fail-closed): Blocks shell injection, chaining, invisible chars
2. **PermissionRegistry**: Risk-based access control (READ_ONLY → DESTRUCTIVE)
3. **Mode enforcement**: PLAN mode = read-only only; BYPASS = all allowed
4. **Agent allowlist**: Per-tool agent restrictions
5. **Metrics tracking**: success/failure rates for anomaly detection

---

*Report generated by architecture explorer agent*
