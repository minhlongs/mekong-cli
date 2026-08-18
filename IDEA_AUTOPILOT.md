# /idea Autopilot — Type Once, Ship Code

> Type the idea exactly once. The autopilot reads the repo, plans, writes
> code, runs tests, checkpoints with claudekit, reflects on failures, and
> iterates until DONE. Worktree-isolated. 1M-token context (DeepSeek).

## TL;DR

```bash
# one-time
bash scripts/idea-init.sh

# every time
mekong idea run "build me a /pricing page that pulls from Polar"
```

That's it. The autopilot creates a worktree at `../mekong-idea-<slug>`,
generates code on branch `idea/<slug>`, and exits with a summary panel.

## How it works

```
┌──────────────────────────────────────────────────────────┐
│  IdeaLoop  (mekong/orchestrator/idea_loop.py)           │
│                                                          │
│  bootstrap → repo_index + system prompt + idea          │
│                                                          │
│  while not safety.exhausted():                          │
│    response = LLM(messages)                             │
│    call     = parse_tool_call(response)                 │
│    result   = dispatch(call)   # READ/WRITE/EDIT/BASH/  │
│                                  TEST/TYPECHECK/        │
│                                  CHECKPOINT/DONE/ABORT  │
│    messages.append(tool_result)                         │
│    if response says DONE → break                        │
│                                                          │
│  if green && --deploy: scripts/deploy-dashboard.sh      │
│  persist context.json + audit.jsonl + result.json       │
└──────────────────────────────────────────────────────────┘
```

Three modules carry the weight:

| Module | Responsibility |
|---|---|
| `idea_loop.py` | The PEV+R loop, audit log, result persistence |
| `context_manager.py` | 1M-token hygiene: lazy file reads, dedupe, compaction at 600k |
| `safety.py` | iter / token / MCU caps, SIGINT cooperative abort |
| `tools.py` | What the LLM can actually do — bash safelist, public-repo boundary, claudekit checkpoint adapter |

## Tools the autopilot has

The LLM emits one tool per turn inside `<tool>…</tool>`. Anything else is
rejected and counts as a failure.

```
READ <path>           lazy-include a repo file
LS [path]             list a directory
WRITE <path>          create/overwrite (body on the next lines)
EDIT <path>           surgical replace (<old>…</old><new>…</new>)
BASH <cmd>            safelisted shell
GIT <subcmd>          git op
TEST                  run pytest / npm test
TYPECHECK             run npm run typecheck or mypy
CHECKPOINT <msg>      claudekit checkpoint, falls back to git commit
DONE <summary>        terminate with success
ABORT <reason>        terminate with failure
```

## Safety bounds (defaults)

| Cap | Default | Override |
|---|---|---|
| Iterations | 12 | `--max-iter` |
| Tokens used | 800k (1M with 200k headroom) | `--max-tokens` |
| MCU credits | 50 | `--max-mcu` |
| Wall-clock | 1 hour | edit `safety.py` `timeout_secs` |
| Consecutive tool failures | 3 → stop | edit `safety.py` |
| Worktree isolation | on | `--in-place` to disable (not recommended) |
| Bash safelist | on | `--unsafe-bash` to disable |
| Forbidden write paths | `apps/`, `mekong/daemon/`, `.env*` | `--override-boundary` |

`Ctrl-C` doesn't kill mid-write — it sets `aborted=True` in the safety
state file. The next loop iteration exits cleanly.

## CLI surface

```
mekong idea run "<idea>" [flags]   # start a run
mekong idea list                   # past runs (50 most recent)
mekong idea show <run-id>          # plan + audit tail + result
mekong idea kill <run-id>          # cooperative abort
```

Flags on `run`:

| Flag | Default | Meaning |
|---|---|---|
| `--max-iter`     | 12 | iteration cap |
| `--max-tokens`   | 800000 | token cap |
| `--max-mcu`      | 50 | MCU credit cap |
| `--worktree` / `--in-place` | worktree | run isolation |
| `--deploy`       | off | run `scripts/deploy-dashboard.sh` if green |
| `--dry-run`      | off | plan only, no writes / shell |
| `--model`, `-m`  | `$LLM_MODEL` | per-run model override |
| `--temp`         | 0.4 | LLM temperature |
| `--unsafe-bash`  | off | disable bash safelist |
| `--yes`, `-y`    | off | skip confirmation |

## LLM endpoints

The autopilot uses Mekong's universal client (`core.llm_client.get_client`),
which auto-detects from these in order:

1. `LLM_BASE_URL + LLM_API_KEY + LLM_MODEL` (universal)
2. `OPENROUTER_API_KEY`
3. `DEEPSEEK_API_KEY`
4. `DASHSCOPE_API_KEY`
5. `ANTHROPIC_API_KEY`
6. `OPENAI_API_KEY`
7. Local Ollama (`LOCAL_LLM_URL`)

Tested combinations:

```bash
# Local DeepSeek via Ollama
export LLM_BASE_URL=http://localhost:11434/v1
export LLM_API_KEY=ollama
export LLM_MODEL=deepseek-v3

# DeepSeek cloud (1M context)
export LLM_BASE_URL=https://api.deepseek.com/v1
export LLM_API_KEY=$DEEPSEEK_API_KEY
export LLM_MODEL=deepseek-chat
```

## The `/idea` slash command (Claude Code IDE)

Existing 25-step blueprint generator at `.claude/commands/idea.md` now ends
with **Phase 7 — Autopilot Hand-Off**: it auto-dispatches
`mekong idea run "<idea> — implement per blueprint"` so the user types
`/idea` once and gets blueprint + working code back without touching the
keyboard again.

Inside Claude Code:

```
/idea solo founder business plan platform with Polar billing
```

→ blueprint phases 1–6 generate `.mekong/company.json` and 5 mission
files → Phase 7 runs `mekong idea run` → autopilot ships the code in a
worktree.

## Files added by this feature

```
.claude/commands/idea.md                   # extended: Phase 7 added
.claude-skills/idea-autopilot/SKILL.md
mekong/orchestrator/__init__.py
mekong/orchestrator/safety.py              # budget caps + kill switch
mekong/orchestrator/context_manager.py     # 1M-token hygiene
mekong/orchestrator/tools.py               # bash safelist + boundary
mekong/orchestrator/idea_loop.py           # PEV+R loop
cli/commands/idea.py                       # mekong idea CLI
src/main.py                                 # +1 add_typer for `idea`
scripts/idea-init.sh                       # claudekit + Ollama setup
package.json                               # +claudekit dep, +scripts
IDEA_AUTOPILOT.md                          # this file
```

## What the autopilot deliberately does NOT do

- **Push or merge.** Founder reviews the worktree diff and merges manually.
- **Edit `apps/` or `mekong/daemon/`.** These are public-repo-boundary
  protected. Use `--override-boundary` if you really mean it.
- **Touch `.env*` files.** Same reason.
- **Run unbounded.** The 4 caps (iter / tokens / MCU / time) plus the
  consecutive-failure brake guarantee a graceful exit.
- **Ask follow-up questions.** It's autonomous. If it doesn't have what
  it needs, it ABORTs with a clear reason.

## Quick smoke test

```bash
mekong idea run "add a /hello command that prints hello world" \
  --max-iter 4 --dry-run -y
```

Output: a plan written to `.mekong/idea/<run-id>/`, no actual writes.
Inspect with `mekong idea show <run-id>`.

## Resume after Ctrl-C

The state file at `.mekong/idea/<run-id>/safety.json` has `aborted=true`.
To pick up where you left off, start a fresh run referencing the
half-built worktree branch:

```bash
mekong idea run "continue the idea/<slug> branch — finish what's left" \
  --in-place                    # already in the worktree
```

The repo index will surface the existing files and the LLM picks up the
trail from there.

## Common failure modes

| Symptom | Likely cause | Fix |
|---|---|---|
| "no `<tool>…</tool>` block" | LLM verbose-mode | lower `--temp 0.2`, retry |
| "REJECTED unsafe bash" | command outside safelist | edit `tools.py SAFE_BASH_PREFIXES` or use `--unsafe-bash` |
| "REJECTED: writes to apps/…" | public-repo boundary | use `--override-boundary` if intentional |
| LLM stuck looping on same file | context not being read | the autopilot already dedupes; if recurring, lower `compact_threshold` in `context_manager.py` |
| "all providers failed" | no `LLM_BASE_URL` configured | run `bash scripts/idea-init.sh` again |
| `claudekit checkpoint` not found | claudekit not installed | `npm i -g claudekit` or just trust the git-fallback path |
