# .claude/_integration/ — Tích hợp / Integration

## VN
Lớp **định nghĩa tích hợp** — commands, agents, skills. CC CLI đọc trực tiếp từ đây.

## EN
**Integration definition layer** — commands, agents, skills. CC CLI reads these directly.

### Contents / Nội dung
| Dir / Thư mục | Mục đích / Purpose |
|---|---|
| `commands/` | 171+ command definitions (.md) — dispatch to `mekong` engine |
| `agents/` | 20 agent definitions (.md) — C-suite + specialist personas |
| `skills/` | 33 skill definitions (SKILL.md) — reusable capabilities |

### How it works / Cách hoạt động
1. CC CLI discovers `.claude/_integration/commands/` at startup / CC CLI khám phá commands khi khởi động
2. Commands dispatch to `mekong` engine (`~/mekong-cli` cwd) / Commands gọi `mekong` engine
3. Skills activate via `/skill-name` or agent prompts / Skills kích hoạt qua slash command hoặc agent prompt
4. Agents override `~/.claude/agents/` (Option B layering) / Agents override stock agents

### Quy tắc / Rules
**DOANH TRẠI (Garrison):** Read-write. Tự do edit.
