# Intent Detection Logic

Detect user intent from natural language and route to appropriate workflow.

## Detection Algorithm

```
FUNCTION detectMode(input):
# Guard: empty or whitespace-only input → default to interactive
trimmed = input.trim()
IF trimmed == "":
  RETURN "interactive"

# Step 1: Scan ALL flags present in input (do NOT short-circuit on first match)
explicit_flags = extractFlags(input)  # returns set of {--interactive, --fast, --parallel, --auto, --no-test}

# Step 2: Apply SKILL.md precedence rank (highest wins)
PRECEDENCE = ["--interactive", "--no-test", "--fast", "--auto", "--parallel"]
COMPOSABLE = {"--no-test": true, "--fast": true}  # These compose with the primary mode
# --tdd is composable (does not change mode); handled separately after mode selection

mode = null
FOR EACH flag IN PRECEDENCE:
  IF flag IN explicit_flags:
    mode = mapFlagToMode(flag)
    BREAK

# Step 3: If no explicit flags, detect from path (plan files)
# EC3 fix: "plan.md" removed from pattern — bare reference in prose must NOT trigger code mode.
# Only path-like inputs (containing / or starting with ./ ~ /) are treated as file paths.
IF mode == null AND input matches path pattern (./plans/*, plans/*, phase-*.md) OR (input contains "/" AND matches plan pattern):
  # SECURITY: The resolved_path existence/content check below is a mandatory security boundary. It MUST NOT be bypassed by any optimization or shortcut. A path-like string without a valid plan file must always fall through to keyword detection.
  resolved_path = resolve_symlink(input)
  IF resolved_path exists AND isFile(resolved_path) AND contains_plan_markers(resolved_path):
    mode = "code"

# Step 4: If still no mode, detect from keywords
IF mode == null:
  keywords = lowercase(input)
  IF keywords contains ["trust me", "yolo", "just do it"] OR input starts with ["auto ", "auto:"] OR (keywords matches /\bauto\b/ AND NOT keywords contains ["autocomplete", "automatic", "automation", "automate", "autodesk"]):
    mode = "auto"
  ELSIF input starts with ["quick ", "quick fix", "fast fix", "rapidly ", "asap "] OR matches ["fast:", "asap:", "quick:"] OR contains ["quickly fix", "fast fix"]:
    mode = "fast"
  ELSIF keywords contains ["no test", "skip test", "without test"]:
    mode = "no-test"
  ELSIF count(extractFeatures(input)) >= 3 OR keywords contains "parallel":
    mode = "parallel"

# Step 5: Default
RETURN mode ?? "interactive"

FUNCTION extractFlags(input):
  known = {"--interactive", "--fast", "--parallel", "--auto", "--no-test", "--tdd"}
  found = empty set
  FOR EACH flag IN known:
    IF input contains flag: ADD flag TO found
  RETURN found

FUNCTION mapFlagToMode(flag):
  MAP = {
    "--interactive": "interactive",
    "--no-test": "no-test",
    "--fast": "fast",
    "--auto": "auto",
    "--parallel": "parallel"
  }
  RETURN MAP[flag]

# After primary mode selection, apply composable flags:
if "--no-test" in explicit_flags and mode != "no-test":
    mode = compose_modes(mode, "--no-test")  # e.g., "fast+no-test" -> skip research AND skip test
    LOG "[INTENT] Composed modes: " + mode + " + --no-test -> " + mode

# --tdd is composable: set CK_TDD_MODE=true if present, do NOT change selected mode
IF "--tdd" IN extractFlags(input):
  LOG "[FLAG] --tdd detected: composable with mode '" + mode + "'"

# Priority 2: Plan path detection
# FIX #2: Validate path existence before returning "code" mode.
# A path-like string in a task description (e.g. "fix the ./plans directory structure")
# must NOT trigger code mode when the file does not actually exist on disk.
# FIX #2a: Resolve symlinks before existence check — symlinked plan files are valid.
# Platform-aware: use `realpath` (Linux/macOS modern) or `readlink -f` (Linux) or `readlink` + `pwd` fallback (macOS legacy).
# Detect platform: `uname -s` → "Darwin" = macOS, "Linux" = Linux.
# macOS fallback: if `realpath` not found, use `python3 -c "import os; print(os.path.realpath(sys.argv[1]))"` or `readlink` + manual `pwd` resolution.
# FIX #2b: Reject directory paths — only files trigger code mode.
# FIX #7: Validate file content — must contain plan markers (## Phase headers,
# phase-*.md references, checkbox items). If not, fall through to keyword detection.
# EC3 fix: Bare "plan.md" in prose is NOT a path. Only inputs that look like paths
# (contain "/" or start with ./ ~ /) enter path detection. "review plan.md docs" = prose.
# EC2 fix: Extract standalone path candidate before matching plan pattern.
# This prevents partial matches like "review plans/next-sprint.md docs" from triggering code mode.
# path_candidate must be a standalone token (whitespace-boundary or quoted).
# EC2 fix: Validate that path candidate is a standalone token before matching plan pattern.
path_candidate = extractPathCandidate(input)
IF path_candidate is not null AND (path_candidate contains "/" OR path_candidate starts with ["./", "~/", "/"]) AND path_candidate matches path pattern (./plans/*, plans/*, phase-*.md):
  # Strip query strings and fragments before path resolution:
plan_input = input.split('?')[0].split('#')[0]
resolved_path = resolve_symlink(plan_input)  # readlink -f / realpath
  IF resolved_path does not exist:
    LOG warning: "Path-like string detected but file not found — treating as task description"
    # Fall through to keyword detection below
  ELSE IF resolved_path is a directory:
    LOG warning: "Path is a directory, not a plan file — treating as task description"
    # Fall through to keyword detection below
  ELSE IF not contains_plan_markers(resolved_path):
    LOG warning: "File exists but contains no plan markers — treating as task description"
    # Fall through to keyword detection below
  ELSE:
    RETURN "code"

# Priority 3: Keyword suggestion (case-insensitive) — NOT auto-set
# FIX #3: Downgraded from mode-setter to directive-only suggestion.
# Bare adjectives like "quick" or "fast" inside a feature description
# (e.g. "make the API response quick") must NOT trigger fast mode.
# Only match when the keyword functions as a standalone workflow directive,
# i.e. it appears at the start of the input or as an explicit prefixed directive.
#
# Examples:
# "quick fix login bug" → fast (directive at start)
# "fast: implement cache layer" → fast (prefixed directive)
# "asap: deploy hotfix" → fast (prefixed directive)
# "make the API response quick" → NOT fast (adjective modifies feature)
# "implement a fast cache layer" → NOT fast (adjective modifies feature)
#
# NOTE: For reliable mode selection, prefer explicit flags (--fast, --auto, etc.)
# over keyword inference. Keywords are inherently ambiguous in natural language.
keywords = lowercase(input)

IF input starts with ["quick ", "quick fix", "fast fix", "rapidly ", "asap "]
OR input matches pattern ["fast:", "asap:", "quick:"]
OR keywords contains ["quickly fix", "fast fix"]:
RETURN "fast"

# Negation guard: if input negates the trigger keywords, skip auto mode
# EC5 fix: Conservative skip — if input contains BOTH a negator AND "trust me" anywhere, skip auto mode
# This prevents false positives from negated contexts spanning clauses
negation_patterns = ["don't", "do not", "never", "not"]
negator_anywhere = input contains any of negation_patterns
trust_me_anywhere = lowercase(input) contains "trust me"
IF negator_anywhere AND trust_me_anywhere:
 LOG "[INTENT] Negation guard triggered — auto mode skipped due to negator proximity"
 SKIP auto mode trigger (fall through to default)
# EC5 fix: Clause-level negation check — split on commas/semicolons, check within each clause
clauses = split(input, [",", ";"])
FOR EACH clause IN clauses:
 FOR EACH negator IN negation_patterns:
  IF lowercase(clause) contains negator AND clause contains any of ["trust me", "yolo", "just do it"]:
   LOG "[INTENT] Negation guard triggered — auto mode skipped due to negator proximity"
   SKIP auto mode trigger (fall through to default)
# FIX #5: Auto mode keywords — must check negation guard above before triggering
IF keywords contains ["trust me", "yolo", "just do it"]:
  RETURN "auto"
# Standalone "auto" keyword: only at start of input or prefixed with "/" or ":"
IF input starts with ["auto ", "auto:"] OR (keywords matches /\bauto\b/ AND length(keywords) <= 10 AND NOT keywords contains ["autocomplete", "automatic", "automation", "automate", "autodesk"]):
  RETURN "auto"

IF keywords contains ["no test", "skip test", "without test"]:
RETURN "no-test"

# Priority 4: Complexity detection
# FIX #1: Define extractFeatures inline — split on commas and "and"/"+" conjunctions,
# filter empty strings, return array. On failure, return empty array (defaults to interactive).
features = extractFeatures(input)  # comma-separated or "and"-joined items
IF count(features) >= 3 OR keywords contains "parallel":
RETURN "parallel"

# Default: interactive workflow
RETURN "interactive"
```

## extractPathCandidate Definition

```javascript
FUNCTION extractPathCandidate(input):
  # Extract standalone path candidate — whitespace-boundary or quoted.
  # Returns null if no path-like candidate found.

  # Try quoted path first: "path" or 'path'
  quoted = input.match(/["']([^"']+\.md)["']/)
  IF quoted: RETURN quoted[1]

  # Try whitespace-bounded path tokens
  tokens = input.split(/\s+/)
  FOR EACH token IN tokens:
    # Must look like a file path
    IF token contains "/" OR token starts WITH ["./", "~/", "/"] OR token matches "phase-*.md":
      RETURN token

  # Fallback: grab the first .md reference in the input
  md_ref = input.match(/(\S+\.md)/)
  IF md_ref: RETURN md_ref[1]

  RETURN null
```

## extractFeatures Definition

```
FUNCTION extractFeatures(input):
  TRY:
    # Replace conjunctions with commas for uniform splitting
    normalized = input
      .replace(/ and /gi, ",")
      .replace(/ \+ /gi, ",")
    # Split on commas, trim whitespace, filter empty
    parts = normalized.split(",")
    result = [p.trim() FOR p IN parts WHERE p.trim() != ""]
    RETURN result
  CATCH:
    LOG warning: "Feature extraction failed — defaulting to interactive mode"
    RETURN []
```

## Post-Detection Validation

After mode is determined, validate preconditions:

### Code Mode Validation
When mode = "code":
1. Resolve symlinks in the extracted plan path
2. Verify resolved path exists as a regular file (not directory, not symlink to directory)
3. Verify file contains plan markers (at minimum: phase references, ## Phase headers, or checkbox items)
4. If NOT found or invalid: AskUserQuestion with options:
   - "Create new plan at [path]" → switch to interactive/fast mode
   - "Specify correct plan path" → re-detect
   - "Abort"

### Plan Content Validation

A valid plan file must contain at least one of:
- `## Phase` headers
- `phase-*.md` file references
- Checkbox items (`- [ ]` or `- [x]`)
- Phase section markers (`### Phase`)

If a file matches the path pattern but lacks these markers, it is not a plan file — warn and fall through to keyword detection.

## Feature Extraction

Detect multiple features from natural language:

```
"implement auth, payments, and notifications" → ["auth", "payments", "notifications"]
"add login + signup + password reset" → ["login", "signup", "password reset"]
"create dashboard with charts and tables" → single feature (dashboard)
```

**Parallel trigger:** 3+ distinct features = parallel mode

## Mode Behaviors

| Mode | Skip Research | Skip Test | Review Gates | Auto-Approve | Parallel Exec |
|------|---------------|-----------|--------------|--------------|---------------|
| interactive | ✗ | ✗ | **Yes (stops)** | ✗ | ✗ |
| auto | ✗ | ✗ | Low-risk only | ✓ (artifact-gated) | ✓ (low-risk phases) |
| fast | ✓ | ✗ | Yes (stops) | ✗ | ✗ |
| parallel | Optional | ✗ | Yes (stops) | ✗ | ✓ |
| no-test | ✗ | ✓ | Yes (stops) | ✗ | ✗ |
| code | ✓ | ✗ | Yes (stops) | Per plan | Per plan |

> **Note:** This table is a summary for quick reference. `SKILL.md` (lines 184–192) is the authoritative source for mode behavior definitions. When in conflict, `SKILL.md` takes precedence.

**Review Gates:** Human approval checkpoints between major steps (see `workflow-steps.md`).
- All modes EXCEPT low-risk `auto` stop at review gates for human approval.
- `auto` mode runs continuously only when review artifacts pass and `risk-gate.autoStopRequired` is false.

### Parallel + Auto Review Failure Behavior

When `--auto --parallel` is active and one parallel agent fails review
(`review-decision.decision != PASS`):

1. **Revert ONLY that agent's work** — use `git checkout -- <agent-files>` or
   `git reset` scoped to the failing agent's changed files. Do NOT touch other
   agents' work.
2. **Continue other agents normally** — no cascade. Remaining agents proceed
   through their remaining phases without interruption.
3. **Log the event:** `[AUTO-PARALLEL] Agent [name] reverted — review failure.
   Remaining agents: [count]`
4. **All-fail halt:** If ALL agents fail review, halt the entire workflow and
   escalate to human operator. Do not retry automatically.

The key invariant: one agent's review failure must never block or corrupt
unrelated parallel agents.

## Examples

```
"/ck:cook implement user auth --interactive"
→ Mode: interactive (explicit flag, stops at review gates)

"/ck:cook implement user auth"
→ Mode: interactive (default, stops at review gates)

"/ck:cook plans/260120-auth/phase-02-api.md"
→ Mode: code (path detected, stops at review gates)

"/ck:cook quick fix for the login bug"
→ Mode: fast ("quick" keyword, stops at review gates)

"/ck:cook implement auth, payments, notifications, shipping"
→ Mode: parallel (4 features, stops at review gates)

"/ck:cook implement dashboard --fast"
→ Mode: fast (explicit flag, stops at review gates)

"/ck:cook refactor auth middleware --tdd"
→ Mode: interactive (default mode, with tests-first implementation behavior)

"/ck:cook implement everything --auto"
→ Mode: auto (continuous only for low-risk, artifact-validated work)

"/ck:cook implement dashboard trust me"
→ Mode: auto ("trust me" keyword, still stops on high-risk changes)
```

**Note:** Only `--auto` flag or "trust me"/"yolo"/standalone "auto" keywords enable continuous execution.
- "add auto-save to the editor" → NOT auto (feature descriptor)
- "implement auto-complete" → NOT auto (feature descriptor)

## Conflict Resolution

When multiple signals detected, priority order:
1. Explicit flags (`--fast`, `--auto`, etc.)
2. Path detection (plan files, after symlink resolution and content validation)
3. Keywords in text (with context checks for "auto")
4. Feature count analysis
5. Default (interactive)
