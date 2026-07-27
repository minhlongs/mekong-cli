# .claude/_core/ — Nhân / Core

## VN
Thư mục **nhân** của Claude Code project. Chứa config, registry, và runtime state.

## EN
Claude Code project **core**. Contains config, registry, and runtime state.

### Contents / Nội dung
| File / File | Mục đích / Purpose |
|---|---|
| `settings.json` | CC CLI permissions, hooks, model routing |
| `agent-registry.json` | Agent definitions registry (model, tools, description) |
| `metadata.json` | Project metadata (version, build info, repo URL) |
| `.ck.json` | ClaudeKit init fingerprint |
| `.ckignore` | CK ignore patterns |
| `.gitignore` | Git ignore (CLAUDE-specific) |
| `.env.example` | Example environment variables |
| `.mcp.json.example` | Example MCP server config |
| `statusline.cjs` | Custom statusline script |
| `agent-memory/` | Agent memory state (pre-compact handoffs, session logs) |
| `session-state/` | Session state cache |
| `worktrees/` | Git worktree runtime state |

### Quy tắc / Rules
**QUÂN DOANH (Fortified):** Config files require `/binh-phap win` before modification.
Các file config cần gate `/binh-phap win` trước khi sửa.
