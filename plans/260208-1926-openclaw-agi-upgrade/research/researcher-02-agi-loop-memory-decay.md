# Research: AGI Loop, NeuralMemory Decay, Telegram Status

**Date:** 2026-02-08 | **Researcher:** researcher-02

---

## Topic 1: Self-Improving AGI Loop Hardening

### 1A. Preventing Repeated Mistakes

**Current gap:** `completed_improvements` is an in-memory list of IDs. If loop restarts, history lost. Gemini may suggest same fix repeatedly.

**Recommended strategies (priority order):**

1. **Bloom Filter / Hash-based dedup** -- Hash each `improvement_id` + `target_files` combo. Store in persistent set (file or NeuralMemory). Before executing, check if hash exists. O(1) lookup, ~zero memory.
2. **Failure blacklist with TTL** -- When improvement fails, store `{improvement_id, fail_count, last_failed_at}`. After 2 failures on same ID, blacklist for 24h. Inject blacklist into `AGI_ASSESS_PROMPT`.
3. **Semantic dedup via NeuralMemory** -- Before executing, query memory: `"AGI improvement similar to: {title}"`. If activation score > 0.85 AND status=FAILED, skip. Already have the infra (`memory_client.query_memory`).
4. **Sliding window for completed list** -- Persist `completed_improvements` to `~/.mekong/agi_history.json`. Load on init. Cap at 100 entries (LRU eviction of oldest).

**Implementation recommendation:** Option 4 (persistent history file) is simplest. Add option 2 (failure blacklist) for robustness. Combined: ~40 lines of code.

```python
# Pseudocode for persistent history
HISTORY_PATH = Path("~/.mekong/agi_history.json").expanduser()

def _load_history(self) -> dict:
    if HISTORY_PATH.exists():
        return json.loads(HISTORY_PATH.read_text())
    return {"completed": [], "blacklist": {}}

def _is_blacklisted(self, improvement_id: str) -> bool:
    bl = self.history["blacklist"].get(improvement_id, {})
    if bl.get("count", 0) >= 2:
        if time.time() - bl.get("last", 0) < 86400:  # 24h
            return True
    return False
```

### 1B. Intelligent Task Prioritization

**Current state:** Gemini picks freely from `IMPROVEMENT_AREAS` list. No weighting.

**Strategies:**

1. **Impact scoring** -- Add weight to each area. Rotate focus: after 3 improvements in same category, force switch. Prevents tunnel vision.
2. **Test-driven priority** -- Run `python3 -m pytest --tb=no -q` before assess. If tests fail, priority = "fix failing tests" (always). If pass, proceed to improvements.
3. **Recency bias** -- Track last-touched category. Penalize recently-touched areas in prompt. Formula: `priority_weight = base_weight * (1 - recency_factor)`.
4. **User-defined priority queue** -- Allow `/agi focus <area>` via Telegram to pin a priority area. Store in config.

**Recommendation:** Option 2 (test-first) is highest-value. If tests broken, nothing else matters.

### 1C. Self-Testing After Each Change

**Current gap:** `_execute()` spawns CC CLI but never runs tests. Success = "CC CLI exited 0", not "code actually works".

**Implementation plan:**

1. After CC CLI completes, run `python3 -m pytest tests/ --tb=short -q` via subprocess
2. Capture exit code + output
3. If tests fail: mark improvement as FAILED, store failure details in memory, trigger rollback (`git checkout -- .`)
4. If tests pass: mark SUCCESS

```python
async def _verify_tests(self) -> tuple[bool, str]:
    proc = await asyncio.create_subprocess_exec(
        "python3", "-m", "pytest", "tests/", "--tb=short", "-q",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd="/Users/macbookprom1/mekong-cli"
    )
    stdout, stderr = await proc.communicate()
    passed = proc.returncode == 0
    output = stdout.decode()[-500:]  # last 500 chars
    return passed, output
```

**Critical:** Must also `git stash` or `git diff` before execution to enable rollback.

### 1D. Adaptive Cooldown

**Current:** Fixed 90s cooldown. 300s after 3 consecutive failures.

**Better approach -- exponential backoff with success acceleration:**

| Condition | Cooldown |
|-----------|----------|
| Success streak >= 3 | `max(30, base * 0.5)` (speed up) |
| Single success | `base` (90s) |
| Single failure | `base * 1.5` (135s) |
| 2 consecutive failures | `base * 3` (270s) |
| 3+ consecutive failures | `base * 5` capped at 600s |

```python
def _calculate_cooldown(self) -> int:
    if self.consecutive_failures == 0:
        streak = self._success_streak()
        if streak >= 3:
            return max(30, self.cooldown // 2)
        return self.cooldown
    return min(self.cooldown * (2 ** self.consecutive_failures), 600)
```

**Also consider:** Time-of-day awareness. During off-hours (midnight-6am), increase cooldown 3x to save API quota.

---

## Topic 2: NeuralMemory Decay Mechanisms

### 2A. Decay Models

**Current state:** Memories persist forever. No eviction. Risk: context pollution as irrelevant old memories crowd out useful recent ones.

**Three viable models:**

| Model | Formula | Best For |
|-------|---------|----------|
| **Exponential decay** | `activation *= e^(-lambda * dt)` | Time-sensitive info (bugs, deployments) |
| **Power-law decay** | `activation *= (1 + dt)^(-alpha)` | Long-term knowledge (slower forget) |
| **Importance-weighted** | `decay_rate = base_rate / importance` | Mixed: important facts persist longer |

**Recommendation for this project:** Importance-weighted exponential decay.

- AGI loop results marked `success=True` get importance=0.8 (slow decay)
- AGI loop results marked `success=False` get importance=0.3 (fast decay -- forget failures quickly)
- User-added memories (`/remember`) get importance=1.0 (minimal decay)
- Default importance=0.5

**Implementation:** Add `decay_pass()` method to `NeuralMemoryClient`:

```python
def decay_pass(self, lambda_base: float = 0.01):
    """Run decay on all memories. Call once per AGI cycle."""
    # POST /api/v1/memory/decay
    # Server-side: multiply each node's activation by decay factor
    # Prune nodes with activation < 0.05
```

**Server-side requirement:** NeuralMemory server needs a `/decay` endpoint. If not available, client-side can track timestamps and filter during `query_memory`.

### 2B. Context Injection Sizing

**Current:** `memory_context[:3000]` chars (hardcoded in `_assess`). Also `max_tokens: 2000` in query.

**Optimal sizing analysis:**

| Model | Max Input | Recommended Context Budget |
|-------|-----------|---------------------------|
| Gemini 2.0 Flash | 1M tokens | 2000-4000 chars (~500-1000 tokens) |
| Gemini 1.5 Pro | 2M tokens | 3000-6000 chars |

**Current 3000 chars is reasonable.** But should be dynamic:

- If no improvements found (assessment returned None): increase to 5000 for next cycle
- If improvement found quickly: decrease to 1500 to save tokens
- Formula: `budget = 1500 + (1500 * miss_streak)` capped at 6000

### 2C. Memory Consolidation

**Problem:** After 100 AGI cycles, memory contains 100+ similar entries like "AGI Loop #42: SUCCESS - Add error handling to X".

**Consolidation strategies:**

1. **Merge-on-encode** -- Before adding new memory, query for similar existing. If cosine similarity > 0.9, update existing node's activation instead of creating new one. Reduces node count.
2. **Periodic summarization** -- Every 20 cycles, ask LLM to summarize last 20 memories into 1 consolidated memory. Delete originals.
3. **Category-based rollup** -- Group memories by `category` metadata. Keep only top-3 per category by activation.

**Recommendation:** Option 1 (merge-on-encode) is cheapest. No extra LLM calls. Spreading activation model already supports node merging conceptually.

```python
def add_memory_deduped(self, content: str, metadata: dict) -> bool:
    existing = self.query_memory(content[:100], depth=1)
    if existing and self._similarity(content, existing) > 0.9:
        return self.boost_memory(existing_id, amount=0.3)
    return self.add_memory(content, metadata)
```

---

## Topic 3: Telegram `/agi status` Enhancement

### Current Output (line 341-349 in telegram_bot.py)

```
Status: Running/Stopped
Iteration: N
Improvements: N
Consecutive failures: N
```

### Recommended Additional Metrics

**Tier 1 (add immediately, data already available):**

| Metric | Source | Format |
|--------|--------|--------|
| Success rate % | `len(completed) / iteration * 100` | `Success Rate: 73%` |
| Last improvement title | `completed_improvements[-1]` (need to store titles, not just IDs) | `Last: "Add retry to executor"` |
| Uptime | `time.time() - start_time` | `Uptime: 2h 14m` |
| Current cooldown | `self.cooldown` | `Cooldown: 90s` |

**Tier 2 (requires tracking additions):**

| Metric | Implementation | Format |
|--------|---------------|--------|
| API calls count | Increment counter in `_assess` + `_execute` | `API Calls: 42` |
| Tokens used (est.) | Track from LLM response metadata | `Tokens: ~85k` |
| Time since last success | Store `last_success_time` | `Last Success: 12m ago` |
| Avg cycle duration | Track `cycle_start/end` times | `Avg Cycle: 3.2min` |
| Categories covered | Set of unique categories from completed | `Categories: 5/15` |

**Tier 3 (nice-to-have):**

| Metric | Value |
|--------|-------|
| Failed improvement IDs (last 3) | Debug visibility |
| Memory node count | NeuralMemory health |
| Disk usage of history | Housekeeping |

### Recommended Status Message Format

```
♾️ *AGI Loop Status*

🟢 Running | Iteration #42
━━━━━━━━━━━━━━━━━━━━
📊 Success: 31/42 (73.8%)
⏱ Uptime: 2h 14m
🕐 Last success: 4m ago
🎯 Last: "Add retry logic to executor"
❌ Consecutive fails: 0
😴 Cooldown: 90s
📂 Categories: 8/15 covered
🧠 Memory nodes: 87
```

### Implementation Changes to `AGILoop`

Need to add these fields to `__init__`:

```python
self.start_time: float = time.time()
self.last_success_time: Optional[float] = None
self.total_api_calls: int = 0
self.completed_details: list[dict] = []  # Store {id, title, category, timestamp}
self.cycle_durations: list[float] = []
```

Then expose via a `get_status() -> dict` method that the Telegram handler calls.

---

## Unresolved Questions

1. **NeuralMemory server API** -- Does it support a `/decay` or `/prune` endpoint? If not, decay must be client-side (less efficient).
2. **Git rollback safety** -- Can AGI loop safely run `git checkout -- .` after failed improvements? What if user has uncommitted changes?
3. **Test suite duration** -- Tests take ~2.5min per MEMORY.md. Running after every AGI cycle adds significant overhead. Consider `pytest --last-failed` or a fast subset.
4. **Token tracking** -- Does `llm_client.py` return usage metadata from the proxy? Need to verify response structure.
5. **Concurrent access** -- If user runs `mekong cook` while AGI loop is modifying files, could cause conflicts. Needs file-level locking or branch isolation.
