# Mekong CLI Command Registry

Single source of truth for all wired commands. Integration point for spec-kit SDD.

## Quick Count

| Tier | Count |
|------|-------|
| Core builtins | 28 |
| Extensions | 12 |
| User presets | 0 |
| Project overrides | 0 |
| **Total wired** | **43** |

## Layer Definitions (PriorityStack)

```
src/config/priority_stack.py -> PRIORITY_STACK.resolve(key)
```

| Layer | Path | Priority |
|-------|------|----------|
| overrides | `.mekong/overrides/` | 1 (highest) |
| presets | `~/.mekong/presets/` | 2 |
| extensions | `src/extensions/` | 3 |
| core | `src/presets/core/` | 4 (lowest) |

## Command Index

| # | Slash | CLI name | Module | Layer |
|---|-------|----------|--------|-------|
| 1 | `/mk cook` | cook | core_commands | core |
| 2 | `/mk agi` | agi | agi | core |
| 3 | `/mk raas` | raas | raas_maintenance_commands | core |
| 4 | `/mk sync-raas` | sync-raas | sync_raas | core |
| 5 | `/mk auth` | auth | auth_commands | core |
| 6 | `/mk license` | license | license_commands | core |
| 7 | `/mk activate` | activate | license_activation | core |
| 8 | `/mk tier-admin` | tier-admin | tier_admin | core |
| 9 | `/mk billing` | billing | billing_commands | core |
| 10 | `/mk monitor` | monitor | monitor | core |
| 11 | `/mk deploy` | deploy | deploy | core |
| 12 | `/mk build` | build | build | core |
| 13 | `/mk test` | test | pytest | core |
| 14 | `/mk lint` | lint | lint | core |
| 15 | `/mk clean` | clean | clean | core |
| 16 | `/mk deploy-all` | deploy-all | deploy.py | core |
| 17 | `/mk usage` | usage | usage_commands | core |
| 18 | `/mk compliance` | compliance | compliance | core |
| 19 | `/mk security` | security | security | core |
| 20 | `/mk vn-setup` | vn-setup | vn_setup | core |
| 21 | `/mk trace` | trace | trace_command | core |
| 22 | `/mk dashboard` | dashboard | dashboard_commands | core |
| 23 | `/mk analytics` | analytics | analytics_commands | core |
| 24 | `/mk docs` | docs | docs | core |
| 25 | `/mk config` | config | config | core |
| 26 | `/mk ci` | ci | ci | core |
| 27 | `/mk workflow` | workflow | workflow_commands | core |
| 28 | `/mk autonomous` | autonomous | autonomous_commands | core |
| 29 | `/mk customer-interview` | customer-interview | customer_interview | extension |
| 30 | `/mk ocop` | ocop | ocop_commands | extension |
| 31 | `/mk tui` | tui | tui/ | extension |
| 32 | `/mk recipe-crawler` | recipe-crawler | recipe_crawler | extension |
| 33 | `/mk lead-hunter` | lead-hunter | lead_hunter | extension |
| 34 | `/mk content-writer` | content-writer | content_writer | extension |
| 35 | `/mk git` | git | git_agent | extension |
| 36 | `/mk file` | file | file_agent | extension |
| 37 | `/mk shell` | shell | shell_agent | extension |
| 38 | `/mk collaborative` | collaborative | tools_browse_collab_commands | extension |
| 39 | `/mk xlsx` | xlsx | xlsx | extension |
| 40 | `/mk update` | update | update_commands | extension |
| 41 | `/mk worktree` | worktree | worktree_commands | extension |
| 42 | `/mk bundle` | bundle | slash alias -> bundle | preset |
| 43 | `/mk spec` | spec | slash alias -> spec | preset |
| 44 | `/mk plan` | plan | slash alias -> plan | preset |
| 45 | `/mk implement` | implement | slash alias -> implement | preset |
| 46 | `/mk doctor` | doctor | diagnostic_commands | core |
| 47 | `/mk rate-limits` | rate-limits | debug_rate_limits | extension |
| 48 | `/mk sync-commands` | sync-commands | sync_commands | core |

## Agent Dispatch Map

Subagents receive commands via slash dispatch (`/mk <agent>`):

```python
AGENT_MAP = {
    "cook": ["plan", "execute", "verify"],
    "agi": ["auto-agent-loop"],
    "monitor": ["health", "status"],
    "deploy": ["cf-workers", "ship"],
    "raas": ["billing", "license", "tier"],
    "usage": ["mcu", "quota", "overage"],
    "lead-hunter": ["discover", "enrich"],
    "content-writer": ["generate", "localize"],
    "recipe-crawler": ["scan", "parse"],
    "spec": ["create", "verify", "bundle"],
    "plan": ["generate", "validate"],
    "implement": ["execute", "converge"],
}
```

## Spec-kit SDD Pipeline Mapping

| spec-kit stage | Mekong command | build-info entrypoint | Verification |
|----------------|----------------|----------------------|--------------|
| `spec` | `mekong spec create` | `mekong spec create` | `mekong spec verify` |
| `plan` | `mekong plan` | `mekong plan` | pytest + ruff |
| `implement` | `mekong implement` | `mekong implement` | make test |
| `converge` | TBD | — | make lint && make test |

## Priority Stack Integration

Commands resolve templates/bundles via `PRIORITY_STACK`:

```python
from src.config import PRIORITY_STACK
template = PRIORITY_STACK.resolve_text(
    key="cook-recipe",
    suffix=".yaml",
    default=Path("src/presets/core/cook-recipe.yaml").read_text()
)
```

Unit of resolution: one file per layer per key.

## Traceability

spec-kit traceability.enforced: false — mapping lives in:
- specDir: specs/ (not yet created)
- mapping: specs/traceability.json (placeholder)

## Change Log

- 2026-08-16 — Initial registry created from 47 command files + spec-kit synthesis
- 2026-08-16 — PriorityStack wired in src/config/__init__.py
- 2026-08-16 — build-info.jsonc updated with specKit section