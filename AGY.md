# AGY CLI

Deep-configured Antigravity stack. See [antigravity-cli/AGY-INTEGRATION.md](antigravity-cli/AGY-INTEGRATION.md) for the full layout.

- **Agent**: `~/.local/bin/agy` (Go binary, 51 hardcoded slash commands)
- **Macro wrapper**: `~/.local/bin/agym` (PTY shim — adds 500+ `/mekong-*` slash macros)
- **Sidecar**: `~/.local/bin/agy-task` → `antigravity-cli/antigravity-cli.py`
- **Plugin install**: `~/.gemini/antigravity-cli/plugins/mekong-cli/` (commands → skills, agents)
- **Config**: `~/.config/agy/` (parallel pool, mirrors opencode) + `~/.antigravity/` (Go runtime)
- **Slash macros (via `agym`)**: `/mekong-<slug>`, `/m-<slug>`, `/mk-list`, `/mk-help`
- **External slash command**: `/agy list | show | plan | walk | new | bin | chat` (in opencode/claude)
