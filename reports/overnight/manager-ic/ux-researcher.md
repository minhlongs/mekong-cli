# UX Researcher Report — Mekong CLI
*Role: UX Researcher | Date: 2026-03-11*

---

## Research Mission

Understand how developers and founders experience Mekong CLI — from first discovery
through daily usage — to identify friction points, unmet needs, and delight moments
that drive retention and word-of-mouth growth.

Primary research question: **What makes someone cook again after their first cook?**

---

## User Mental Models

### Mental Model 1: "It's like a smarter shell script"
Developers map Mekong CLI to their existing model of shell scripting + Make.
- Expectation: deterministic, fast, composable
- Mismatch: LLM non-determinism surprises them ("why did it do it differently this time?")
- Design implication: Show the plan before executing — `--dry-run` should be a common entry point

### Mental Model 2: "It's like an AI assistant I give tasks to"
Founders and less technical users think of it as a VA or chatbot.
- Expectation: natural language input, conversational feedback
- Mismatch: terminal UX feels harsh when things fail (raw error messages)
- Design implication: Friendly error messages with suggested fixes ("Did you mean: mekong fix?")

### Mental Model 3: "It's a framework I need to learn"
Advanced developers see the 289 commands as a system to master.
- Expectation: deep documentation, examples for every command
- Mismatch: documentation is sparse beyond README
- Design implication: In-terminal `mekong help cook --examples` with real output samples

---

## Usability Testing Plan

### Study 1: First-Time User Activation (TTFC Study)
**Goal:** Measure and reduce time from pip install to first successful cook.
**Method:** Moderated remote session, screen recording + think-aloud
**Participants:** 5 developers, 3 non-technical founders
**Tasks:**
1. Install Mekong CLI following only the README
2. Configure an LLM provider of their choice
3. Run `mekong cook "Create a Python function that sums a list"`
4. Interpret the output and confirm success

**Metrics:**
- Time to complete each task (seconds)
- Number of errors / confusion moments
- Task success rate (0/1)
- SUS (System Usability Scale) score post-session

**Predicted pain points:**
- Step 2: 3 separate `export` commands without a wizard
- Step 3: Unclear what "cook" means to non-devs
- Step 4: Rich terminal output overwhelming for non-devs

---

### Study 2: Command Discovery (Learnability Study)
**Goal:** How do users find and learn new commands from the 289-command catalog?
**Method:** Unmoderated task-based testing via Maze or UserTesting
**Participants:** 10 developers who have used Mekong CLI at least 3 times
**Tasks:**
1. "Find the command to generate an annual business plan"
2. "Find the command to review your code quality"
3. "Find a command you've never used before that looks useful"

**Metrics:**
- Task completion rate
- Time on task
- Commands discovered per session
- `mekong help` usage frequency

---

### Study 3: Mission Output Comprehension (Error Study)
**Goal:** When a `mekong cook` fails, do users understand why and what to do next?
**Method:** Moderated session with failure scenarios injected
**Participants:** 5 developers (mixed seniority)
**Scenarios to test:**
- LLM API key not configured (most common new user failure)
- Verifier fails (test didn't pass)
- Rollback triggered (step failed mid-execution)

**Key question:** "What would you do next?" after each failure message.

---

## User Interview Guide

### Screener Questions
1. Do you use any CLI tools in your daily development workflow?
2. Have you used any AI coding assistants (Copilot, Cursor, Cody)?
3. How comfortable are you configuring environment variables in a terminal?
4. What operating system do you primarily use for development?

### Interview Questions (45 minutes)

**Section 1: Context (10 min)**
- Walk me through a typical day in your development workflow.
- What are the most repetitive tasks you do each week?
- What does "done" look like for a typical task?

**Section 2: First Impressions (10 min)**
- What made you try Mekong CLI?
- What was your first impression when you saw the README?
- Describe your first `mekong cook` experience.

**Section 3: Usage Patterns (15 min)**
- Which commands do you use most often? Which do you avoid?
- When does Mekong CLI help you most? When does it fall short?
- Has it ever surprised you — positively or negatively?

**Section 4: Mental Models (10 min)**
- If you had to explain Mekong CLI to a colleague in one sentence, what would you say?
- How do you think about the Plan → Execute → Verify loop?
- What would make you use it every single day?

---

## Heuristic Evaluation

Quick pass against Nielsen's 10 heuristics for the CLI UX:

| Heuristic | Status | Finding |
|-----------|--------|---------|
| Visibility of system status | Partial | Progress shown in verbose mode; silent in default |
| Match between system/real world | Poor | "MCU", "PEV", "cook" — jargon-heavy for new users |
| User control and freedom | Good | `--dry-run` provides safe exploration |
| Consistency and standards | Good | All commands follow `mekong [command] "[goal]"` |
| Error prevention | Poor | No validation before LLM call (e.g., empty API key) |
| Recognition over recall | Poor | 289 commands require memorization; no autocomplete |
| Flexibility and efficiency | Good | `--verbose`, `--json`, `--strict` flags for power users |
| Aesthetic and minimalist design | Good | Default output is clean; verbose adds detail |
| Help users recover from errors | Poor | Error messages are raw Python exceptions |
| Help and documentation | Poor | `mekong help` exists but examples are sparse |

**Top 3 fixes (effort vs impact):**
1. Validate API key before first LLM call — show friendly message if missing
2. Improve error messages: wrap Python exceptions in human-readable text
3. Add `mekong help [command] --examples` with real terminal output samples

---

## Key UX Metrics to Track

| Metric | Measurement Method | Frequency |
|--------|-------------------|-----------|
| SUS score | Post-session survey | Per study |
| TTFC | Session recording timer | Monthly |
| Task success rate | Moderated sessions | Per study |
| Error recovery rate | Session recording | Per study |
| NPS (Net Promoter Score) | In-app prompt after 3rd cook | Monthly |
| Feature discovery rate | PostHog `command_used` events | Weekly |

---

## Research Roadmap (Q2 2026)

| Month | Study | Output |
|-------|-------|--------|
| April | Study 1 (TTFC) — 8 participants | Report + `mekong init --wizard` spec |
| April | Heuristic eval on CLI error messages | 10 prioritized improvements |
| May | Study 2 (command discovery) — 10 participants | Navigation redesign recommendations |
| June | Study 3 (error recovery) — 5 participants | Error message rewrite spec |
| June | NPS baseline survey (first 100 users) | NPS score + verbatim themes |

---

## Immediate Research Actions

- [ ] Recruit 5 developer participants for Study 1 (GitHub issues commenters, Discord members)
- [ ] Set up session recording tool (Loom for unmoderated, Zoom for moderated)
- [ ] Run heuristic evaluation on current CLI error messages (solo, 2 hours)
- [ ] Draft SUS survey for post-session use
- [ ] Instrument PostHog to capture command usage distribution (which of 289 are used)
- [ ] Set up NPS prompt triggered after 3rd successful cook
