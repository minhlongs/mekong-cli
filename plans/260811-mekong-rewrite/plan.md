# Mekong CLI 7.0 — Full Rewrite Plan

**Ngày:** 2026-08-11 · **Priority:** HIGH · **Status:** DONE — v7 implemented & verified live
**Quyết định:** Rewrite hoàn toàn từ đầu, lấy ak CLI làm hoa tiêu, model qua OmniRoute gateway.

## Kết quả (verified 2026-08-11)

- ✅ `mk doctor` — 6/6 OK (gateway, fable, opus, haiku, strategist)
- ✅ `mk ask` / `mk strategist` — qwen3.8-max trả chiến lược chuẩn
- ✅ `mk plan` — plan.md + 17 phase files tạo
- ✅ `mk debug` — root cause + fix steps (sonnet bị meta-narration → map sang opus)
- ✅ `mk cook` — PEV + tool-calling (write/cat/bash) tạo file thật + verify
- ✅ Agent registry YAML — fix indentation lỗi, 6 agents load
- ✅ `~/bin/mk` wrapper — bỏ .claude-mk chết, gọi thẳng .venv
- ✅ Slash commands `/ak:cook` `/ak:fix` `/ak:plan` `/mk:fix` — đúng đích

## Context / Lý do

- Mekong 6.0.0: 319 commands, 22MB src + 32MB harness TS, nhánh WIP `kongming-kill-list-5.0.0` — quá phình, không vận hành được (`mk` wrapper chết, `/ak:fix` sai đích, harness TS giả lập agent).
- Hoa tiêu ak 2.4.0: vài command lifecycle (init/doctor/kit/update), output json/plain/pretty, exit codes chuẩn — KISS.
- Mục tiêu: CLI mới chạy được, ít command mạnh, agent thật (gọi LLM), model map đúng zuneF/gateway.

## Kiến trúc mới (7.0)

```
mekong-cli/
├── src/
│   ├── main.py              # Typer app entry (giữ, sửa nhẹ)
│   ├── core/
│   │   ├── llm.py           # LLM client qua OmniRoute (SSE stream + tool call)
│   │   ├── models.py        # Model registry: fable/sonnet/opus/haiku/qwen38 → gateway id
│   │   ├── agents.py        # Agent registry + dispatch (model per agent)
│   │   ├── pev.py           # Plan-Execute-Verify engine (checkpoint/resume)
│   │   ├── config.py        # ~/.mekong/config.json (gateway URL, token, model)
│   │   └── doctor.py        # Health check (gateway ping, model test)
│   ├── commands/
│   │   ├── init.py          # mk init → setup config + .agentkit/ownership
│   │   ├── doctor.py        # mk doctor → kiểm tra gateway + models
│   │   ├── cook.py          # mk cook <task> → PEV pipeline
│   │   ├── cook_auto.py     # mk cook-auto <goal> (checkpoint)
│   │   ├── cook_parallel.py # mk cook-auto-parallel <goal>
│   │   ├── plan.py          # mk plan <task> → plan.md + phase files
│   │   ├── debug.py         # mk debug <issue> → fix plan (dry-run/execute)
│   │   ├── ask.py           # mk ask <q>
│   │   ├── list.py          # mk list → recipes
│   │   └── search.py        # mk search <q>
├── agents/registry.yaml     # giữ (sun-tzu/ceo/ae/pm/eng/ops + model)
├── recipes/                 # giữ
├── plans/                   # giữ
├── sops/                    # giữ
└── harness/                 # XOÁ (TS harness cũ — thay bằng Python core)
```

## Model mapping (qua OmniRoute)

| Vai trò | Model id gửi gateway | Combo resolve |
|---|---|---|
| Session chính / light | `claude-fable-5` | claude-fable-5 (zuneF free) |
| Agent sonnet (ceo/ae/pm/eng/ops) | `claude-sonnet-5-0` | combo sonnet-5-0 |
| Heavy command (cook/fix/plan) | `claude-opus-4-8` | combo opus-4-8 |
| Subagent nhanh | `claude-haiku-4-5` | combo haiku (mới) |
| Strategist (sun-tzu) | `strategist` | qwen3.8-max |

Env: `ANTHROPIC_BASE_URL=http://omnimbp.local:20128/api`, `ANTHROPIC_AUTH_TOKEN=sk-...`, `ANTHROPIC_MODEL=<per-call>`.

## LLM client (llm.py)

- OpenAI-compatible `POST /api/v1/messages` (Anthropic format) hoặc `/api/v1/chat/completions`
- SSE stream, tool calling, timeout 120s, retry 2
- Hỗ trợ `stream=false` cho JSON structured output

## Agent dispatch (agents.py)

- Đọc `agents/registry.yaml` (giữ) — model field chuẩn
- Dispatch: gọi LLM với system prompt agent + tools (Read/Write/Bash qua subprocess)
- Sun-tzu: `strategist` combo → qwen3.8-max

## Commands chi tiết

1. **init** — tạo `~/.mekong/config.json`, test gateway, `ak init` ownership
2. **doctor** — ping gateway, test từng model, báo trạng thái (giống ak doctor)
3. **cook <task> [--auto]** — PEV: plan → execute (agents) → verify → report
4. **cook-auto <goal>** — checkpoint/resume (state file `~/.mekong/state/<goal>.json`)
5. **cook-auto-parallel <goal>** — 4 phase agents song song (independent) + verify
6. **plan <task> [--hard]** — tạo `plans/YYYYMMDD-name/plan.md` + phase files
7. **debug <issue> [--execute]** — phân tích + fix plan (dry-run default)
8. **ask <q>** — một lượt hỏi model
9. **list / search** — recipes catalog

## Xoá

- `harness/` (TS) — thay bằng Python core
- `src/old/`, `src/engine/` nếu có
- Wrapper `~/bin/mk` → gọi thẳng `.venv/bin/mekong` (bỏ .claude-mk)

## Wrapper / Slash commands

- `~/bin/mk` → `exec $MEKONG_ROOT/.venv/bin/mekong "$@"` (bỏ .claude-mk)
- `/ak:fix` → `mekong debug $ARGUMENTS`
- `/ak:cook` → `mekong cook $ARGUMENTS`
- `/mk:fix` → `mekong debug $ARGUMENTS`
- `/mk:cook` → `mekong cook $ARGUMENTS`

## Success criteria

1. `mk doctor` → tất cả model OK (fable/sonnet/opus/haiku/strategist)
2. `mk debug "bug x"` → plan tạo, không lỗi
3. `mk cook "tạo file x"` → PEV hoàn tất
4. `@kongming` qua strategist → qwen3.8-max (đã verify)
5. `/ak:fix` chạy được trong Claude Code

## Risks

- Rewrite mất tính năng 319 command cũ → chỉ giữ command thiết yếu (7.0 = MVP)
- Agent tự gọi Bash/Write: cần sandbox/allowlist an toàn
- Timeout: model chậm (qwen38 120s) — đã có per-model timeout

## Next steps

1. Build core: llm.py + models.py + config.py + main.py
2. Commands: init/doctor/ask/list/search
3. PEV: plan/debug/cook
4. Agents + parallel
5. Wrapper + slash commands
6. Test end-to-end
