# Mekong CLI — Demo Script & Flow

## Demo Purpose
Show prospective users/investors the full PEV loop in action across 3 personas:
1. Non-technical founder: business plan generation
2. Developer: cook + verify + rollback
3. Team lead: CI/CD gate with Qwen (cost control)

**Total runtime:** 12 minutes
**Setup required:** `.env` with `LLM_BASE_URL` + `LLM_API_KEY`, Python 3.9+, `pip install mekong-cli`

---

## Pre-Demo Checklist

```bash
# 1. Verify install
mekong version   # should print v0.x.x

# 2. Verify LLM connection
mekong health    # should show LLM: OK

# 3. Reset demo state
rm -rf /tmp/demo-project
mkdir /tmp/demo-project && cd /tmp/demo-project
git init

# 4. Set Ollama for offline demo fallback
export OLLAMA_BASE_URL=http://localhost:11434/v1
export LLM_MODEL=qwen2.5-coder
```

---

## SCENE 1: The Founder (3 min)

**Narrative:** "Imagine you're a founder with an idea. You don't code. Let's see what Mekong does."

### Step 1.1 — Business validation
```bash
mekong founder/validate "Micro-SaaS for Vietnamese small restaurant POS"
```
Expected output:
- Market size estimate (SEA F&B SMB)
- 3 customer segments
- Top 5 jobs-to-be-done
- Preliminary PMF score: 0–100
- Recommended next step

**Talk track:** "This is running a structured customer discovery analysis. Notice it doesn't just give generic advice — it's specific to Vietnamese restaurant operators."

### Step 1.2 — Annual plan
```bash
mekong annual "Year 1 plan for RestaurantOS Vietnam"
```
Expected output: 12-month milestone roadmap, revenue targets, hiring plan, key risks.

**Talk track:** "A founder without a team just generated a board-ready annual plan in 90 seconds."

### Step 1.3 — Show dry-run (optional, if time)
```bash
mekong annual "Year 1 plan" --dry-run
```
**Talk track:** "Dry-run shows the plan before any LLM tokens are consumed. MCU cost: 0 for the plan itself, 3 MCU to execute."

---

## SCENE 2: The Developer (5 min)

**Narrative:** "Now let's switch to a developer. Same tool, different layer."

### Step 2.1 — Bootstrap a project
```bash
cd /tmp/demo-project
mekong cook "Create a FastAPI REST API with JWT auth and a /users endpoint" --dry-run
```
Expected dry-run output:
```
Plan (7 steps):
  1. Create project structure
  2. Install fastapi, pyjwt, uvicorn
  3. Implement main.py with app setup
  4. Implement auth.py with JWT encode/decode
  5. Implement users.py router
  6. Write tests/test_users.py
  7. Verify: pytest + lint
```

**Talk track:** "Before spending a single MCU, we see the full execution plan. Step 7 is verification — Mekong runs tests itself."

### Step 2.2 — Execute
```bash
mekong cook "Create a FastAPI REST API with JWT auth and a /users endpoint"
```
Live output (annotate as it runs):
- `[PLAN]` — steps appear
- `[EXEC step 1]` — project structure created
- `[EXEC step 3]` — main.py written (show: `cat src/main.py`)
- `[VERIFY]` — pytest runs
- `[DONE]` — success + MCU deducted

**Talk track:** "Watch step 7. It actually runs pytest. If tests fail, the orchestrator retries with a corrected prompt before giving up."

### Step 2.3 — Simulate a failure + rollback
```bash
# Introduce a bug manually
echo "def broken(): return 1/0" >> src/main.py

mekong fix "Tests failing after main.py edit" --verbose
```
Expected output:
- Verifier detects test failure
- `[ROLLBACK]` reverses broken edit
- `[RETRY]` applies corrected patch
- `[VERIFY]` passes

**Talk track:** "This is the PEV loop in action. Plan → Execute → Verify — and when verify fails, it rolls back and self-heals. No other open-source CLI tool does this."

### Step 2.4 — Review gate
```bash
mekong review
```
Expected output: code quality report, 0 critical issues, 2 suggestions.

---

## SCENE 3: The Team Lead / CI Context (3 min)

**Narrative:** "Now let's see how a team uses this in CI — and how to control costs."

### Step 3.1 — Cost switch to Qwen
```bash
export LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
export LLM_MODEL=qwen2.5-coder-32b-instruct
# $10/month flat rate vs $39/seat Copilot Enterprise

mekong review --strict   # same command, Qwen model
```
**Talk track:** "Same review command. Different model. Qwen is $10/month unlimited. GitHub Copilot Enterprise is $39/seat. A 10-person team saves $380/month."

### Step 3.2 — Show status + AGI score
```bash
mekong status --verbose
```
Expected output:
```
Mekong CLI v0.x.x
LLM: qwen2.5-coder-32b @ dashscope [OK]
MCU Balance: 847 / 1000 (Pro tier)
AGI Score: 78/100
  ✓ Planning accuracy: 85%
  ✓ Execution success: 91%
  ✗ Verification coverage: 62% (target: 80%)
Last mission: "FastAPI REST API" — SUCCESS (3 MCU)
```

**Talk track:** "AGI score is Mekong's self-assessment. 78/100 means it's tracking toward enterprise quality. The verification gap is the next sprint focus."

### Step 3.3 — Plugin system preview
```bash
mekong plugin list           # see available plugins
mekong plugin install demo-audit   # hypothetical install
mekong demo-audit            # run custom command
```
**Talk track:** "The plugin system lets teams add company-specific commands. Your internal security policy, your specific test runner, your custom deploy target — all as `mekong` commands."

---

## Q&A Cheat Sheet

| Question | Answer |
|----------|--------|
| "What if the LLM is wrong?" | PEV verifier catches errors; rollback reverts bad steps |
| "Can I use my own LLM?" | Yes — any OpenAI-compatible endpoint, including local Ollama |
| "How is this different from Aider?" | Aider: code suggestions only. Mekong: plan + execute + verify + rollback + business layer |
| "Is it open source?" | MIT license — fork, extend, white-label |
| "What's the cost?" | Free with Ollama; or $49–499/mo for RaaS credits |
| "Can it run in CI?" | Yes — pure CLI, no IDE required |
| "289 commands — where do I start?" | `mekong cook` (developers) or `mekong annual` (founders) |

---

## Demo Reset

```bash
rm -rf /tmp/demo-project
unset LLM_BASE_URL LLM_MODEL
# Restore your normal .env
```

---

## Brainstorm: Demo Variants

- **Investor demo (5 min):** Scene 1 only + AGI score + billing tiers
- **Developer demo (8 min):** Scene 2 full + rollback emphasis
- **Agency demo (10 min):** `company/init` + `marketing` + `sales` pipeline
- **Conference lightning talk (3 min):** Single `cook` command live, show rollback, show Qwen swap

---

_Demo owner: OpenClaw CTO_
_Last rehearsed: 2026-03-11_
_Record: `mekong cook --verbose > demo-recording.log 2>&1`_
