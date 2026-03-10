# Mekong CLI Plugin Developer Guide

> v3.1 | Sources: `src/core/plugin_loader.py`, `plugin_registry.py`, `plugin_validator.py`

## 1. Overview

Plugins extend mekong-cli without modifying core code. Two load sources:
- **Local**: `~/.mekong/plugins/my_plugin.py` — drop in, no install needed
- **PyPI**: `pip install mekong-plugin-x` — distributed, version-controlled

Plugin failures are **never fatal** — logged as warnings, CLI continues.

| Type | Purpose | Entry Point Group |
|------|---------|-------------------|
| `agent` | Custom Plan-Execute-Verify agent | `mekong.agents` |
| `provider` | LLM/API backend | `mekong.providers` |
| `hook` | Lifecycle callbacks (pre/post task) | `mekong.hooks` |
| `recipe` | YAML task templates | `~/.mekong/recipes/` |

---

## 2. Quick Start (3 Steps)

**Step 1 — Create plugin file:**

```python
# my_seo_agent.py
from mekong.core.agent_base import AgentBase
from mekong.core.executor import ExecutionResult


class SeoAgent(AgentBase):
    def plan(self, goal: str) -> list[dict]:
        return [{"action": "shell", "cmd": f"curl -sI {goal}"}]

    def execute(self, steps: list[dict]) -> ExecutionResult:
        return ExecutionResult(exit_code=0, stdout="SEO audit complete")

    def verify(self, result: ExecutionResult) -> bool:
        return result.exit_code == 0


def register(registry) -> None:
    """Required entry point — called by PluginLoader."""
    registry.register("seo", SeoAgent)
```

**Step 2 — Install locally:**
```bash
cp my_seo_agent.py ~/.mekong/plugins/
```

**Step 3 — Use it:**
```bash
mekong agent seo "https://example.com"
```

No restart needed — mekong discovers plugins on every run.

---

## 3. Plugin Interface

Every plugin **must** define `register(registry)` at module top level:

```python
def register(registry) -> None:
    """
    Called by PluginLoader during discovery.
    registry: AgentRegistry (agent plugins) or PluginRegistry (provider/hook)
    Must NOT raise — wrap in try/except if needed.
    """
    registry.register("my-plugin-name", MyPluginClass)
```

The validator checks via AST before any execution:
- `register` must exist at module level
- `register` must be callable
- File name must not start with `_`

---

## 4. Plugin Types

### Agent Plugin

Implement `AgentBase` — Plan → Execute → Verify pattern:

```python
from mekong.core.agent_base import AgentBase
from mekong.core.executor import ExecutionResult


class ContentAgent(AgentBase):
    def plan(self, goal: str) -> list[dict]:
        return [
            {"action": "llm", "prompt": f"Write a blog post about: {goal}"},
            {"action": "shell", "cmd": "echo done"},
        ]

    def execute(self, steps: list[dict]) -> ExecutionResult:
        output = [f"[LLM] {s['prompt']}" for s in steps if s["action"] == "llm"]
        return ExecutionResult(exit_code=0, stdout="\n".join(output))

    def verify(self, result: ExecutionResult) -> bool:
        return result.exit_code == 0 and len(result.stdout) > 0


def register(registry) -> None:
    registry.register("content", ContentAgent)
```

### Provider Plugin

Supply LLM backends — registered via `mekong.providers` entry point:

```python
import os, openai


class DashScopeProvider:
    name = "dashscope"
    base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    def complete(self, messages: list[dict], model: str = "qwen3-coder-plus") -> str:
        client = openai.OpenAI(api_key=os.environ["DASHSCOPE_API_KEY"], base_url=self.base_url)
        resp = client.chat.completions.create(model=model, messages=messages)
        return resp.choices[0].message.content


def register(registry) -> None:
    registry.register("dashscope", DashScopeProvider)
```

### Hook Plugin

Lifecycle callbacks — registered via `mekong.hooks` entry point:

```python
import logging, time

class TimingHook:
    def pre_execute(self, task: dict) -> None:
        task["_start"] = time.time()

    def post_execute(self, task: dict, result) -> None:
        logging.info("Task finished in %.2fs", time.time() - task.get("_start", 0))

def register(registry) -> None:
    registry.register("timing", TimingHook)
```

### Recipe Plugin

YAML task template placed in `~/.mekong/recipes/`:

```yaml
# ~/.mekong/recipes/deploy-cloudflare.yaml
name: deploy-cloudflare
steps:
  - action: shell
    cmd: "wrangler deploy --env production"
  - action: shell
    cmd: "curl -sI https://my-worker.workers.dev"
    verify: {expected_output: "HTTP/2 200"}
```
```bash
mekong run deploy-cloudflare
```

---

## 5. Installation Methods

### Local file

```bash
cp my_plugin.py ~/.mekong/plugins/
```

Via Python API:
```python
from mekong.core.plugin_registry import PluginRegistry
from pathlib import Path

registry = PluginRegistry()
manifest = registry.install_local(Path("my_plugin.py"))
# copies to ~/.mekong/plugins/, computes SHA-256 checksum
```

### PyPI package

```bash
pip install mekong-plugin-seo
```

Via Python API:
```python
manifest = registry.install("mekong-plugin-seo")  # runs pip install
```

### Uninstall

```python
registry.uninstall("my-plugin")
# local: deletes ~/.mekong/plugins/my_plugin.py
# pypi:  runs pip uninstall -y
```

---

## 6. Security Requirements

`PluginValidator` scans via AST. **Violations block loading.**

### Banned — cause ERROR (plugin rejected)

```python
import subprocess    # banned
import pickle        # banned
import marshal       # banned
eval("code")         # banned
exec("code")         # banned
os.system("cmd")     # banned (via import os.system)
__import__("...")    # banned
```

### Hardcoded secrets — cause WARNING

```python
# Flagged by regex scanner:
API_KEY = "sk-abc123..."          # warning
STRIPE_SECRET_KEY = "sk_live_..."  # warning
```

Always use environment variables:
```python
import os
api_key = os.environ.get("MY_PLUGIN_API_KEY")
```

### Allowed

```python
import os          # ok (os.environ, os.path — not os.system)
import pathlib, json, logging, re  # ok
import requests, httpx, openai     # ok
```

---

## 7. Validation

Run before submitting:

```python
from mekong.core.plugin_validator import PluginValidator
from pathlib import Path

validator = PluginValidator()
result = validator.validate_all(Path("my_plugin.py"))
print("Valid:", result.is_valid)
print("Errors:", result.errors)     # block activation
print("Warnings:", result.warnings) # informational
```

Validation pipeline (in order):
1. **Syntax** — `ast.parse()` — no code execution
2. **Security** — AST walk for banned imports + regex for secrets
3. **Interface** — loads module, confirms `register` callable
4. **Dependencies** — `importlib.util.find_spec()` per dep (optional)

```python
# Check dependencies separately
result = validator.validate_dependencies(["requests>=2.28", "pydantic>=2.0"])

# Quick one-liner
from mekong.core.plugin_validator import validate_plugin
is_valid, msg = validate_plugin(Path("my_plugin.py"))
```

---

## 8. Publishing to PyPI

### Project structure

```
mekong-plugin-seo/
├── pyproject.toml
└── mekong_plugin_seo/
    ├── __init__.py
    └── agent.py
```

### pyproject.toml

```toml
[project]
name = "mekong-plugin-seo"
version = "1.0.0"
requires-python = ">=3.9"
dependencies = ["requests>=2.28"]

[project.entry-points."mekong.agents"]
seo = "mekong_plugin_seo.agent:SeoAgent"

# Provider plugins:
# [project.entry-points."mekong.providers"]
# dashscope = "mekong_plugin_dashscope.provider:DashScopeProvider"

# Hook plugins:
# [project.entry-points."mekong.hooks"]
# timing = "mekong_plugin_timing.hook:TimingHook"

[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.backends.legacy:build"
```

The module must expose `register(registry)` (same as local plugins). Use `mekong-plugin-<name>` naming for discoverability.

```bash
pip install build twine && python -m build && twine upload dist/*
```

---

## 9. API Reference

### PluginRegistry

```python
from mekong.core.plugin_registry import PluginRegistry, PluginType, PluginStatus

r = PluginRegistry()                               # loads ~/.mekong/plugin_registry.json
r.discover()                                       # scan local + entry_points
r.install("mekong-plugin-seo")                    # pip install + register
r.install_local(Path("plugin.py"))                 # copy to ~/.mekong/plugins/
r.validate("plugin-name")                          # -> (bool, str)
r.activate("plugin-name", loader)                  # load into runtime
r.deactivate("plugin-name")                        # mark disabled (restart to unload)
r.uninstall("plugin-name")                         # delete file / pip uninstall
r.list_plugins(plugin_type=PluginType.AGENT)       # filter by type
r.list_plugins(status=PluginStatus.ACTIVE)         # filter by status
r.get("plugin-name")                               # -> PluginManifest | None
r.count                                            # int
```

### PluginManifest key fields

| Field | Type | Notes |
|-------|------|-------|
| `name` | str | unique registry key |
| `version` | str | semver |
| `plugin_type` | PluginType | AGENT \| PROVIDER \| HOOK \| RECIPE |
| `source` | str | "local" \| "pypi" \| "git" |
| `status` | PluginStatus | AVAILABLE \| INSTALLED \| ACTIVE \| DISABLED \| ERROR |
| `checksum` | str | SHA-256 first 16 chars (local only) |
| `error_message` | str | last error when status == ERROR |

### PluginLoader

```python
from mekong.core.plugin_loader import PluginLoader, DEFAULT_PLUGIN_DIR
# DEFAULT_PLUGIN_DIR = Path.home() / ".mekong" / "plugins"

loader = PluginLoader(agent_registry=my_registry)
loader.discover_all()                        # entry_points + local dir
loader.discover_local(Path("/custom/path"))  # custom directory
loader.list_plugins()                        # list[dict] name/source/type
loader.plugin_count                          # int
```

### PluginValidator

```python
from mekong.core.plugin_validator import PluginValidator, validate_plugin

v = PluginValidator()
result = v.validate_all(Path("plugin.py"))   # runs all checks
result.is_valid; result.errors; result.warnings

v.validate_syntax(path)          # AST parse, no execution
v.validate_security(path)        # banned imports + secrets scan
v.validate_interface(path)       # register() callable check
v.validate_dependencies(["requests"])  # importlib availability

is_valid, msg = validate_plugin(path)  # convenience one-liner
```

---

## Pre-publish Checklist

- [ ] `register(registry)` exists at module top level and is callable
- [ ] No banned imports: `subprocess`, `eval`, `exec`, `os.system`, `pickle`, `marshal`
- [ ] No hardcoded secrets — use `os.environ`
- [ ] `validate_plugin(path)` returns `True`
- [ ] Entry point group matches type: `mekong.agents` / `mekong.providers` / `mekong.hooks`
- [ ] Package named `mekong-plugin-<name>`, dependencies in `pyproject.toml`
