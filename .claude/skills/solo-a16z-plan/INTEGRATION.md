# Solo a16z Plan — ClaudeKit Integration

A guided 14-section / 61-card business-plan workflow for solo founders, built
around the Andreessen Horowitz lens (Idea Maze, Why Now, 7 Powers, LTV/CAC,
distribution-first, founder-market fit). The same data drives:

- the **CLI** — `claude plan-a16z ...`
- the **skill** — `.claude/skills/solo-a16z-plan/` (auto-discovered)
- the **dashboard** — `/solo-a16z` route under `apps/dashboard`

State is one JSON file per project at `.claude/solo-a16z/<slug>.json`. CLI and
dashboard both read and write that file, so you can switch between terminal
and IDE freely.

---

## Files added

```
.claude/skills/solo-a16z-plan/
  SKILL.md                              # skill metadata (CC auto-discovers)
  framework.json                        # 14 sections / 61 cards / prompts (single source of truth)
  INTEGRATION.md                        # this file

cli/commands/plan_a16z.py               # Typer sub-app `plan-a16z`
cli/entrypoint.py                       # +1 import, +1 add_typer (already wired)

apps/dashboard/app/(founder)/solo-a16z/page.tsx     # Next.js route /solo-a16z
apps/dashboard/app/api/solo-a16z/route.ts           # GET/POST state to .claude/
apps/dashboard/public/embeds/solo-a16z-plan.html    # standalone HTML platform (iframed)
```

No existing files were modified except `cli/entrypoint.py` (one new sub-app
registration).

---

## 10-minute setup checklist

1. **Verify framework loads**
   ```bash
   python3 -c "from cli.commands import plan_a16z; \
       fw = plan_a16z._load_framework(); \
       print(f'{len(fw)} sections, {sum(len(s[\"cards\"]) for s in fw)} cards')"
   ```
   Expect: `14 sections, 61 cards`.

2. **Verify CLI is wired**
   ```bash
   claude plan-a16z --help
   ```

3. **Run a smoke test (no LLM call)**
   ```bash
   claude plan-a16z init "Tôi đang xây [idea]…"
   claude plan-a16z list
   claude plan-a16z show idea_maze.0
   ```

4. **First real LLM card** (uses your existing `LLM_BASE_URL` / `LLM_API_KEY` / `LLM_MODEL`)
   ```bash
   claude plan-a16z run idea_maze.0 -y
   ```

5. **Burst a whole section**
   ```bash
   claude plan-a16z run-section idea_maze
   claude plan-a16z run-section customer
   ```

6. **Export the plan**
   ```bash
   claude plan-a16z export -f md -o plan.md
   claude plan-a16z export -f json -o plan.json
   ```

7. **Open the dashboard mirror** (optional)
   ```bash
   cd apps/dashboard && npm run dev
   # then: claude plan-a16z dashboard   (opens http://localhost:3000/solo-a16z)
   ```

---

## CLI surface

| Command | What it does |
| --- | --- |
| `plan-a16z init "<seed>"` | Save the seed idea (everything else feeds from this). |
| `plan-a16z list [-s <section_id>]` | Tabular status of every card. |
| `plan-a16z show <key>` | Print a card's resolved prompt + current result. `--prompt` for raw piping. |
| `plan-a16z run <key> [-y]` | Call the LLM for one card and store the result. |
| `plan-a16z run-section <id>` | Run every card in a section in dependency order. |
| `plan-a16z set <key> -` | Pipe a result in from stdin (e.g. paste output from elsewhere). |
| `plan-a16z export -f md|json [-o file]` | Export the whole plan. |
| `plan-a16z status` | One-line progress summary. |
| `plan-a16z dashboard` | Open the dashboard route in a browser. |

All commands accept `--project <slug>` so a single founder can hold several
plans side by side (`raise-seed`, `wedge-product`, `pivot-2`, …).

---

## Section ids (for `--section` and `run-section`)

```
seed              0. Seed
idea_maze         1. Idea Maze
customer          2. Customer
problem           3. Problem & Solution
market            4. Market (TAM/SAM/SOM)
distribution      5. Distribution & GTM
unit_economics    6. Unit Economics
moat              7. Moat & Defensibility
brand             8. Brand & Messaging
content           9. Content Engine
roadmap          10. Roadmap
risk             11. Risk
ask              12. The Ask
wisdom           13. Wisdom Council
```

Card keys are `<section_id>.<index>`; e.g. `customer.3` is the Beachhead
Persona card.

---

## How CLI and dashboard stay in sync

The standalone HTML in `apps/dashboard/public/embeds/solo-a16z-plan.html`
keeps its in-progress state in `localStorage`. When loaded inside the
dashboard iframe (with `?bridge=1`) a small bridge script:

1. Posts `solo-a16z:ready` to the dashboard on load.
2. Listens for `solo-a16z:hydrate` and replaces local state with the file
   contents read from `.claude/solo-a16z/<project>.json`.
3. Hooks `localStorage.setItem` and posts `solo-a16z:state` (debounced 500 ms)
   on every save.

The dashboard's API route `/api/solo-a16z` reads/writes the same file the CLI
uses. So `claude plan-a16z run idea_maze.0` and clicking a card in the
browser produce the same artifact on disk.

---

## LLM client

The CLI uses `core.llm_client.get_client()` (or `src.core.llm_client.get_client()`
as a fallback), which respects the standard 3-var setup:

```bash
export LLM_BASE_URL=https://openrouter.ai/api/v1
export LLM_API_KEY=sk-or-v1-...
export LLM_MODEL=anthropic/claude-sonnet-4
```

Override per-call with `--model` and `--temp` on `run` / `run-section`.

The HTML platform also has an optional OpenAI key field (Settings ⚙️) for the
"Generate" button when the user opens the HTML directly without the CLI.
Inside the dashboard iframe, the recommended path is still the CLI / dashboard
route because they share the filesystem state.

---

## Where to extend

- **Add a new card**: edit `.claude/skills/solo-a16z-plan/framework.json`,
  add an entry to the appropriate section's `cards` array. CLI and dashboard
  pick it up on next reload — no code changes.
- **Add a new section**: append a new section object with a fresh `id`. Make
  sure `input_ref`s of downstream cards reference the new id correctly.
- **Custom prompts per project**: add a `framework.<project>.json` and switch
  `_load_framework()` to read it when `--project` is set. (Not implemented;
  worth doing if you ship multiple verticals.)
- **Hook into OpenClaw**: `claude plan-a16z run-section` is already a single
  shell call — easy to wrap as a Mission step in `core/openclaw/missions/`.

---

## Removing the integration

```bash
# revert the wire-in
git checkout cli/entrypoint.py

# delete added files
rm -rf .claude/skills/solo-a16z-plan
rm cli/commands/plan_a16z.py
rm -rf apps/dashboard/app/\(founder\)/solo-a16z
rm -rf apps/dashboard/app/api/solo-a16z
rm apps/dashboard/public/embeds/solo-a16z-plan.html
# state files (keep these if you want to preserve plans)
rm -rf .claude/solo-a16z
```
