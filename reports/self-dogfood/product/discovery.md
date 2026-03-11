# Product Discovery — Mekong CLI v5.0

**Date:** March 2026 | **Stage:** Pre-scale discovery | **Method:** Jobs-to-be-done + segment hypothesis

---

## The Core Question

Who actually needs a 289-command AI business CLI that can plan a sprint, write copy, generate a pitch deck, and deploy code — all from the terminal?

The answer is not "everyone who uses AI." It is a specific set of people who (1) live in the terminal already, (2) run or manage a business function, and (3) are frustrated that their AI tools help them think but don't help them execute.

---

## Market Segments

### Segment 1: Technical Solo Founders (Primary)

**Size estimate:** ~800K globally (Indie Hackers has 600K registered, Product Hunt ~500K daily actives with strong founder overlap)

**Profile:**
- Full-stack developer, 3–10 years experience
- Building a SaaS, tool, or agency solo or with 1 co-founder
- Monthly AI spend: $50–$150 (Cursor + ChatGPT + maybe Copilot)
- Bottleneck: switching between code tools and business tools constantly

**The gap Mekong fills:** They can ship code with Cursor. They cannot `cursor plan-sprint` or `cursor write-investor-update`. Mekong is the missing layer — business execution from the terminal where they already live.

**Discovery signal:** Indie Hackers threads titled "I replaced my entire morning routine with ChatGPT" get 500+ upvotes. The demand is real; the execution is still manual.

---

### Segment 2: Digital Agency Owners (Secondary — higher ACV)

**Size estimate:** ~200K agencies globally with 1–20 employees

**Profile:**
- Agency billing $15K–$150K/month
- Repeats the same 30% of every project (auth, CI/CD, env setup, client brief → PRD translation)
- Has developers who want to build, not scaffold
- Would pay $149/month without question if Mekong saves 5 hours/month

**The gap Mekong fills:** Agencies sell time. Every hour saved on boilerplate is margin. The white-label API + custom recipe angle makes Mekong a "product" they can resell or embed in their delivery process.

**Discovery signal:** "How do I automate my dev workflow" is one of the top 10 searches in agency Slack communities.

---

### Segment 3: Internal Dev Teams at Startups (Emerging — Enterprise path)

**Size estimate:** ~50K startups with 3–20 engineers who would consider a CLI-based automation layer

**Profile:**
- Series A startup, 5–20 engineers
- Already using GitHub Copilot + some AI code review
- Wants to standardize how AI is used across the team (not each dev prompting ChatGPT differently)
- DevOps/platform engineer is the buyer; individual devs are users

**The gap Mekong fills:** Standardized AI workflows across a team. A shared recipe library. One credit pool. Not each engineer paying their own ChatGPT subscription.

**Discovery signal:** "How do we give our team access to AI without everyone just doing their own thing" — Enterprise tier demand.

---

## Jobs-to-be-Done Analysis

### Job 1: "Help me go from idea to shipped faster" (Functional)

**Current solutions people hire:** ChatGPT for planning, Cursor for code, Vercel for deploy, ClickUp for tasks. Each requires context switching.

**Mekong's JTBD answer:** `mekong plan → cook → test → deploy` is a complete loop. The user never leaves the terminal. The plan feeds the cook. The cook produces deployable output.

**Friction in current solution:** Context lost between tools. A plan written in ChatGPT doesn't connect to the code Cursor writes. Mekong's PEV engine (Plan→Execute→Verify) keeps the context chain intact.

---

### Job 2: "Run my business without hiring someone for every function" (Functional)

**Current solutions:** Upwork for one-off tasks, Fiverr for content, agency retainers for strategy.

**Mekong's JTBD answer:** 289 commands covering Founder, Business, Product, Engineering, and Ops layers means one tool handles what would otherwise be 5 different hires or services.

**Evidence from command distribution:**
- Founder layer: `annual`, `okr`, `swot`, `fundraise`, `pitch` — replaces a strategy consultant
- Business layer: `sales`, `marketing`, `finance` — replaces fractional heads
- Ops layer: `audit`, `health`, `security` — replaces a DevOps consultant

---

### Job 3: "Get consistent quality without managing people" (Emotional)

**Core anxiety:** Every time a solo founder delegates to a freelancer, they spend 2 hours reviewing and fixing the output. They'd rather do it themselves if the tool was good enough.

**Mekong's JTBD answer:** The Verify layer of PEV runs quality gates automatically. Output isn't just generated — it's checked. This reduces the anxiety of "will this actually be usable?"

---

### Job 4: "Look and operate like a bigger team than I am" (Social)

**Core desire:** A 1-person operation that delivers agency-quality output.

**Mekong's JTBD answer:** DAG workflow recipes are the pre-built playbooks that large teams use but small teams don't have time to create. Running `mekong marketing` gives a solo founder the same structured approach a 5-person marketing team would use.

---

## Discovery Interview Framework

### Target Respondents

- 5 technical solo founders (1-person teams, building SaaS)
- 3 agency owners (5–20 person shops)
- 2 dev team leads at Series A startups

### Interview Structure (45 minutes)

**Warm-up (5 min)**
- "Walk me through a typical work week. What does your morning look like?"
- "What tools do you open first when you sit down to work?"

**Current workflow (15 min)**
- "When you need to write a technical spec or plan a feature, what do you do?"
- "Tell me about the last time you had to do something business-y — like write a proposal or figure out pricing. How did that go?"
- "What did you try first? What did you end up doing?"
- "Where did you get stuck?"

**AI usage today (10 min)**
- "What AI tools are you currently paying for? What do you actually use them for?"
- "Tell me about a time an AI tool disappointed you. What happened?"
- "Have you tried to use AI for anything beyond writing code? What was that like?"

**Concept probe (10 min)** *(show the `mekong cook` demo)*
- "What's your immediate reaction?"
- "Who would you show this to first?"
- "What would make you nervous about using this for real work?"
- "What's missing that would make this a must-have?"

**Closing (5 min)**
- "If this tool worked exactly as described, what's the first thing you'd use it for?"
- "What would you pay for this? Why?"
- "Is there anyone else you know who'd care about this?"

---

## Discovery Hypotheses to Validate

| Hypothesis | Signal to look for | Invalidation signal |
|------------|-------------------|---------------------|
| Terminal-native users self-select | Respondents already use CLI for deploys/git | Respondents prefer GUI-only workflows |
| Cross-layer pain is real | People describe switching between 3+ tools for one task | People say their current stack is fine |
| $49/mo feels cheap vs. current spend | Current AI spend exceeds $49 | People balk at $49 as expensive |
| PEV loop is the differentiator | People react to "it verifies the output" | People only care about generation speed |
| Recipe library has standalone value | People ask to browse recipes before buying | Nobody cares about recipes |

---

## Findings Template (fill post-interviews)

**Most common JTBD cited:** ___
**Biggest current pain with existing tools:** ___
**Surprise insight:** ___
**Willingness to pay — median:** ___
**Segment with strongest pull:** ___
**Feature most requested that doesn't exist:** ___
**Biggest adoption blocker:** ___

---

## Next Steps After Discovery

1. Synthesize into updated persona cards (update `persona.md`)
2. Identify top 3 use cases with strongest pull → prioritize in v5.1 sprint
3. Build demo around the winning use case, not the full 289-command surface
4. If agency segment shows highest ACV signal → prioritize white-label API in roadmap
