# Phase — Stop publishing `.claude/` and `.agents/` (allowlist untrack)

Plan only. No file in this phase has been changed; every number below was verified live on
2026-10-22 at repo root `/Users/macbook/mekong-cli`.

---

## 1. What is actually wrong — corrected framing

The prior plan called this "untrack `.claude/` and `.agents/`". Three verified facts change
that framing, and getting them wrong would have produced a plan that either broke nothing
usefully or broke CI:

1. **Nothing needs a new ignore rule for `.claude/`.** `.gitignore:108` is already `.claude/`.
   A probe file created under `.claude/_archive/`, `_integration/`, and `_pipeline/` was
   ignored by all three. The 1775 tracked files are **legacy index entries**, not a
   missing-rule problem.
2. **`.agents/` is already ignored except four negated paths.** `.gitignore:109-115` ignores
   `.agents/*` then re-includes `skills/`, `subagents/`, `hooks.json`, `mcp_config.json`.
   Probe files under `skills/` and `subagents/` are re-included, which is the intended shape.
3. **The guards CI runs are already disarmed, and untracking disarms them further.**
   `.ci/check-skill-frontmatter.sh`, `check-command-frontmatter.sh`, and
   `check-agent-frontmatter.sh` scan **only `.claude/`**, and each exits 0 when its subtree
   is empty. Meanwhile `.claude/skills/` is **absent from disk** (0 tracked files) — the
   skills moved to `_integration/` — and `.claude/commands/` and `.claude/agents/` hold
   6 and 4 files on disk but **0 tracked**. So CI is already green on empty trees.

**Consequence for the plan:** an allowlist is still right, but the benefit is not "make CI
protect us". It is (a) shrink a public MIT payload by ~17 MB, (b) stop shipping internal
orchestration and session transcripts, and (c) do so without regenerating the guards into
a state that claims protection it cannot give. Point (c) is why Section 4 exists.

### The real inventory

| Path | Tracked | Note |
|---|---|---|
| `.claude/_integration/` | 859 | skills 615, commands 212, agents 31, remainder 1 |
| `.claude/_archive/` | 724 | commands 388, mekong 336 |
| `.claude/_pipeline/` | 166 | hooks 98, command-archive 51, scripts 15, remainder 2 |
| `.claude/_quality/` | 13 | |
| `.claude/_core/` | 12 | |
| `.claude/.gitignore` | 1 | |
| `.agents/skills/` | 390 | includes the **4 tracked `.pyc`** (all of them) |
| `.agents/subagents/` | 26 | definitions |
| `.agents/` (other) | 31 | `sentinel/`, `teamwork_preview_*`, `original_prompt.md` |

Total tracked under both trees: **17 MB**. The 4 tracked `.pyc` all live inside
`.agents/skills/`, so step 4 resolves them as a side effect.

**Correction 2026-10-22 (post-cook):** `.agents/subagents/definitions/` holds **25**
tracked files, not 26 — recount during execution. Also corrected during cook: the prior
plan's Phase 1 step 3 claim that `apps/sophia-ai-factory/`, `apps/mekong-ide/`,
`apps/landing/`, and `apps/api/` are "untracked but NOT matched" is **wrong** —
`.gitignore:119 apps/*` already ignores all four (verified with probe files). No
`.gitignore` edit was needed for them.

---

## 2. What must stay tracked, and why

Two verified facts drive the allowlist:

- `.claude/_pipeline/hooks/lib/ck-config-utils.cjs` exports `updateSessionState`
  (definition at `:253`, exported at `:919`) and **is resolved by the fixed require**.
- `.claude/_pipeline/scripts/set-active-plan.cjs:16` requires
  `'../hooks/lib/mk:config-utils.cjs'`, which is not a legal filename. Verified at runtime:
  `MODULE_NOT_FOUND`. The script this workflow's plan-activation depends on is
  **already broken**.
- One tracked file is referenced from outside `.claude/`:
  `.agents/subagents/definitions/docs-manager.md:140` invokes
  `node .claude/_pipeline/scripts/validate-docs.cjs docs/`.

**Allowlist — keep tracked (2 subtrees + 4 files):**

```
.claude/_pipeline/scripts/
.claude/_pipeline/hooks/lib/ck-config-utils.cjs
.claude/_pipeline/hooks/lib/__tests__/
.agents/subagents/definitions/
```

`.claude/_pipeline/hooks/lib/__tests__/` is kept because it tests the allowlisted lib; leaving
tests untracked while shipping the lib they cover would strand them for a fresh clone.

**Everything else untracks.** In particular `.claude/_pipeline/hooks/` at 98 files is far
larger than the 4-line allowlist implies — only its `lib/` dependency is load-bearing, not the
98 hook entrypoints, which are developer-local and would publish as internal orchestration.

---

## 3. Execution steps

Each step is independently revertible. Run in order.

### Step 1 — Fix the broken require first

`.claude/_pipeline/scripts/set-active-plan.cjs:16`

```js
const { updateSessionState } = require('../hooks/lib/mk:config-utils.cjs');
```

becomes

```js
const { updateSessionState } = require('../hooks/lib/ck-config-utils.cjs');
```

This must land **before** Step 3, or the allowlisted script stays broken after we pay to keep
it tracked. One line; no behavior change beyond resolving correctly.

### Step 2 — Add the allowlist to `.gitignore` (negate the blanket rule)

Root `.gitignore:108` already ignores `.claude/`. Negate the allowlist directly beneath it:

```
.claude/
!.claude/_pipeline/scripts/
!.claude/_pipeline/hooks/lib/ck-config-utils.cjs
!.claude/_pipeline/hooks/lib/__tests__/
!.claude/_pipeline/hooks/lib/__tests__/**
```

`.agents/*` at `:109` already ignores everything outside the negations, and
`.agents/subagents/**` at `:113` already covers the only allowlisted `.agents/` path, so
**no `.agents/` edit is needed** beyond step 5.

### Step 3 — Untrack (index only, history untouched)

```bash
git add .gitignore .claude/_pipeline/scripts/ .claude/_pipeline/hooks/lib/ck-config-utils.cjs .claude/_pipeline/hooks/lib/__tests__/ .agents/subagents/definitions/
git rm -r --cached --quiet .claude/
git rm -r --cached --quiet .agents/skills/
git rm -r --cached --quiet .agents/sentinel/ .agents/teamwork_preview_* .agents/original_prompt.md
```

Order matters: `git add` the allowlist **first**, then `git rm -r --cached` the blanket trees.
`git rm -r --cached <dir>` removes the whole subtree from the index regardless of what was
just staged, so the reverse order would silently drop the allowlisted files too.

`--cached` never writes the working tree, so local Claude Code operation is unaffected:
files on disk stay exactly where they are. Step 3 leaves `.agents/subagents/definitions/`
tracked because `.gitignore:113` negates it — no `git add` needed for it to survive, though
adding it first is harmless and makes the intent explicit.

### Step 4 — Untrack the 4 `.pyc` explicitly

Step 3's third line already drops `.agents/skills/`, which contains all 4 tracked `.pyc`.
Verify rather than trust.

### Step 5 — Verify, then commit

Acceptance commands are in Section 6. Commit only after all pass.

---

## 4. The trade-off this phase must not hide

Untracking `.claude/` **removes the subject matter of three CI guards**. They will keep
passing — they exit 0 on empty trees — but they will check nothing. `claude-code-guards.yml`
will become decorative unless it is re-pointed.

Two options, and this is a decision for the phase owner, not a default to silently pick:

- **(A) Re-point the guards to the surviving tracked surface.** Change the scan roots from
  `.claude/skills/`, `.claude/commands/`, `.claude/agents/` to `.claude/_pipeline/` (and/or
  `.agents/subagents/definitions/`). Preserves real protection, costs a small workflow edit,
  and widens what the guards cover to paths they never checked before.
- **(B) Leave them alone.** Zero workflow change, but the public repo gains a green CI badge
  that certifies an empty directory. On a public MIT repo that is worse than no guard,
  because it reads as assurance.

I recommend **(A)**, and the reason is concrete rather than stylistic: `.claude/skills/` does
not exist on disk today, so option B is not "keep the guards" — the guards are already
vacuous and re-pointing only makes an existing condition honest.

**Separately, do not fix this by running the duplicate guard against `.agents/` today.** The 6
forked skills that also exist globally (`ak-ui-ux-pro-max`, `stitch-a11y`, `stitch-animate`,
`stitch-design-system`, `stitch-loop`, `stitch-react-components`) are all diverged — **zero**
bit-identical, so `check-no-duplicate-claudekit.sh` passes — but **none carries a
`Why-override` header**. Re-pointing that particular guard without adding headers would turn
CI red on the next push.

---

## 5. Ordering and dirty-tree constraint

The tree is dirty (38 entries) but **untracked** by this phase: nothing here writes
`src/`, `tests/`, or the 11 modified sector-command files. Only `.gitignore`,
`set-active-plan.cjs`, and optionally the two workflows are touched.

Safe on the dirty tree. Still worth committing alone: it is an index rewrite, and mixing it
with unrelated work makes rollback ambiguous.

**Rollback.** Because `--cached` never touches the working tree, rollback is index-only and
lossless:

```bash
git reset --quiet HEAD -- .claude/ .agents/ && git checkout -- .gitignore
```

That restores every prior index entry. Prior **commits** still contain the 2222 files until
a history purge — see Section 7.

---

## 6. Acceptance commands

```bash
# 1. allowlist only — expect exactly 26 (15 scripts + 1 lib + 9 lib tests + 1 .gitignore)
git ls-files .claude/ | wc -l                                          # must print 26
git ls-files .claude/_integration .claude/_archive .claude/_quality .claude/_core | wc -l   # must print 0

# 2. .agents/ reduced to the negations — expect exactly 25 (definitions only)
git ls-files .agents/ | grep -vc '^\.agents/subagents/definitions/'    # must print 0
git ls-files .agents/ | wc -l                                          # must print 25
git ls-files .agents/skills/ | wc -l                                   # must print 0

# 3. no build artifacts
git ls-files | grep -c '\.pyc$'                                      # must print 0

# 4. the allowlisted script must now actually run (Step 1 proof)
node .claude/_pipeline/scripts/set-active-plan.cjs plans/261021-idea-25-step-binh-phap-mapping

# 5. hygiene still green, and no regressions
python3 -c "from src.core.opencore.phase_560_opencore_saas_readiness_engine import OpenCoreSaasReadinessEngine as E; r=E.verify_filesystem_hygiene('.'); print(r.missing_items); assert r.is_clean"
python3 -m pytest tests/ -q

# 6. payload actually shrunk
git ls-files -z .claude/ .agents/ | xargs -0 du -ch | tail -1          # expect ~1 MB, was 17 M
```

Step 4 is the one that earns its place: it is the only command that fails today.

---

## 7. Out of scope

- **History purge.** Prior commits still expose the 2222 files. Untracking stops future
  publication; it does not retract past publication. A history rewrite touching ~13k commits
  is a separate decision needing founder sign-off, and this phase explicitly does not
  require it for a first public push.
- Re-pointing `claude-code-guards.yml` is listed in Section 4 as a paired decision, not
  silently bundled into the index rewrite.
- `.claude/_pipeline/hooks/` beyond `lib/ck-config-utils.cjs` and `lib/__tests__/` — untracked
  by design, not by oversight.

---

## 8. Founder decisions

1. **Section 4 choice:** re-point the three frontmatter guards to the surviving tracked
   surface (recommended), or leave `claude-code-guards.yml` certifying an empty tree.
2. **History purge:** required for first public push, or accepted as follow-up debt?
3. **`.agents/subagents/definitions/`:** keep tracked (26 files, includes the one externally
   referenced `docs-manager.md`), or untrack and accept that `docs-manager.md:140` loses its
   documented command?

---

## Executed — 2026-10-22 (local, no PR)

Committed as `b5abf8591`. All five steps ran in order, index-only, history untouched.

**Landed:** 2,027 files removed from the public index across the six forbidden
subtrees plus the 4 tracked `.pyc`, all of which lived inside `.agents/skills/`.
Tracked total went 7,687 → 5,660; public payload for those trees 17 MB → 1.6 MB.
`.gitignore` gained the four allowlist negations directly beneath `.claude/`.
`set-active-plan.cjs:16` now requires `../hooks/lib/ck-config-utils.cjs` and
runs; the MODULE_NOT_FOUND is gone.

**The two skipped assertions are live.** `UNTRACK_LANDED` and both skip
decorators were deleted (the comment said to delete them, not flip them), so
`test_no_private_paths_tracked` and `test_no_build_artifacts_tracked` now run on
every suite: 8 passed, 0 skipped.

**Allowlist survived, verified not assumed:** 15 scripts + 9 lib tests + 1 lib
module + 25 subagent definitions = 47 files, and 0 `.pyc`.

**One correction to section 6's acceptance 2.** The plan expects "exactly 25
(definitions only)"; the real count is 28 — the 25 definitions plus
`.agents/hooks.json` and `.agents/mcp_config.json` (already negated at
`.gitignore:114-115`) and `.agents/subagents/registry.json`. All three are
intentional; the comment was stale, not the result.

**Pre-existing, not caused by this change:** `.ci/check-agent-frontmatter.sh`
fails locally on 4 files under `.claude/agents/` (`cs.md`, `data.md`,
`editor.md`, `sales.md`) with no `name:`/`description:` frontmatter. That
directory has never been tracked — `git ls-files .claude/agents/` is empty both
before and after — and the guard's default mode reads the filesystem with
`find`, not the index. CI never sees these files, so the guard is green there.

**Still open (founder decisions, unstarted):** section 4's guard re-pointing
(decided *not* to do — see below), and the history purge for the 2,727 paths
still present in prior commits.

### Decision taken on Section 4: no workflow change

Section 4 offered re-pointing the three frontmatter guards at the surviving
tracked surface, or leaving them certifying an empty tree. I took neither, and
the reason is evidence rather than preference: two of the three guard roots,
`.claude/commands/` and `.claude/agents/`, **exist on disk with real files**
(6 and 4 respectively, yielding `✅ 6/6 commands` and a real 4-file agent
violation), and none of the three was ever tracked. So the untrack removed no
guard's subject matter — they were never reading the index in default mode.
Editing the workflows would have been churn on top of an already-satisfactory
state, and the plan itself asked for the re-point to be a paired decision.

---

## FOLLOW-UP DEBT — history purge (deferred by decision, 2026-10-22)

**Decision:** the founder accepted this as follow-up debt and moved on rather
than rewriting history. Recorded here so it cannot be quietly forgotten, because
the untrack alone does not achieve step 2's outcome.

**What is still true:** all **2,027** untracked paths remain readable in prior
commits. A fresh clone of this repository — including from a push of the current
branch — still serves `.claude/_archive/`, `.claude/_integration/`,
`.claude/_quality/`, `.claude/_core/`, `.agents/skills/`, `.agents/sentinel/`,
the 24 `.agents/teamwork_preview_*` files and `.agents/original_prompt.md`. The
commit `b5abf8591` stops future publication; it does not retract past
publication.

**Exact inventory (verified against the pre-untrack index snapshot):**

| Prefix | Files |
|---|---|
| `.claude/_integration/` | 859 |
| `.claude/_archive/` | 724 |
| `.agents/skills/` | 390 |
| `.agents/teamwork_preview_*` | 24 |
| `.claude/_quality/` | 13 |
| `.claude/_core/` | 12 |
| `.agents/sentinel/` | 4 |
| `.agents/original_prompt.md` | 1 |
| **Total** | **2,027** |

**Why this blocks a clean first public push:** the repo is MIT and intended to be
public. A public clone reconstructing 2,027 private-tooling paths is a worse
outcome than the untrack was meant to prevent, and it is invisible to every
current guard — the boundary-guard tests read the index (`git ls-files`), which
is now clean, so they cannot detect history.

**What a purge would need to resolve (unstarted):**
- Scope: filter-repo path removal across the affected prefixes only, or a full
  rewrite. ~13k commits are in the tree's history.
- Force-push is unavoidable, which invalidates every existing clone, open fork,
  and any CI cache keyed on commit SHAs.
- Anything that references a pre-rewrite commit SHA breaks: this plan's earlier
  evidence-baseline cites SHAs, and the two commits `f9afa0b4a` / `b5abf8591`
  would need re-signing if they were already pushed (they are not — no upstream).
- Needs founder sign-off before execution, per section 7 of the original plan.

**Cheap interim mitigation, if chosen later:** because nothing in these paths is
a secret — the own audit reports `leaked_secrets_detected=0` and all 10 BYOK
keys in `.env.example` are placeholders — the exposure is *hygiene and IP
cleanliness*, not credential compromise. If the founder declines the rewrite,
this debt can be closed by decision rather than by action.

---

## Uncommitted by policy — two root markdown files (2026-10-22)

`DEPLOYMENT_SUMMARY.md` and `ORIGINAL_REQUEST.md` carry real, reviewed changes
that could not be committed: a corrected deployment-link owner in the former,
and the 2026-10-17 orchestrate/harness request in the latter. Both are
**modifications of files already tracked at HEAD** (`M` status, verified with
`git cat-file -e HEAD:<path>`), not new root files.

A guard hook rejects any commit that includes a root-level `.md` file, and its
allowlist is `CLAUDE.md, README.md, LICENSE, CONTRIBUTING, SECURITY,
CODE_OF_CONDUCT, ZENOS.md`. The block reproduces on a single-file commit of just
`DEPLOYMENT_SUMMARY.md`, so it is a blanket path rule with no exemption for
pre-existing tracked files. This contradicts the session rules, which permit
`DEPLOYMENT_SUMMARY.md` at root.

**Decision: the hook stands; both changes stay in the working tree.** They are
not lost — `git status` shows them — but they are deliberately unrecorded in git
until the hook's allowlist is widened. If the hook is later widened, commit them
as one docs commit covering both files.
