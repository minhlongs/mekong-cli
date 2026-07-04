---
name: plan-ceo-review
description: "CEO-level plan review: product-market fit, 10-star vision, market timing analysis"
model: opus
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - WebSearch
triggers:
  - ceo review
  - business review
  - strategy review
  - think bigger
  - scope expansion
---

# Plan CEO Review

## When to invoke

Rethink the problem, find the 10-star product, challenge premises, expand scope when it creates a better product.
Use when asked to "review the strategy", "think bigger", "is this ambitious enough", or "check the business plan".

## Workflow

### Step 1: Context Gathering

Read these files (if they exist):
- The plan or spec being reviewed
- `ZENOS.md` -- economic particle constitution
- `AI/ceo.md` -- CEO agent definition
- `AI/decisions/` -- prior decision log

### Step 2: Product-Market Fit Assessment

Rate the plan on five dimensions:

| Dimension | Score (0-10) | Notes |
|-----------|-------------|-------|
| Problem validation | /10 | Is this a real pain point? Who feels it? |
| Solution clarity | /10 | Can the user describe what it does in one sentence? |
| Market timing | /10 | Why now? Would 6 months ago or 6 months later be wrong? |
| Target audience | /10 | Who exactly? ICP defined or vague? |
| Competitive moat | /10 | Why can't someone copy this in a week? |

For each score below 7: state the gap, describe what a 10 looks like, present as opt-in to Founder.

### Step 3: 10-Star Product Vision

Ask the three framing questions:

1. **10x check:** What's the version that's 10x more ambitious but only 2x more effort?
   - Describe it concretely, not abstractly.
   - What would the user feel when using it?
2. **Platonic ideal:** If the best team in the world had unlimited resources, what would this become?
3. **Delight scan:** What 5 adjacent 30-minute improvements would make this feature sing?
   - Where would a user think "oh nice, they thought of that"?

Output: Proposals for Founder to opt in/out of, each with effort estimate.

### Step 4: Market Timing Analysis

```
+------------------+        +------------------+        +------------------+
| Market readiness | -----> | Solution fit     | -----> | Timing advantage |
| Is the market    |        | Does this solve   |        | Why now? What    |
| educated on this |        | it better than    |        | makes this the   |
| problem?         |        | existing options? |        | right moment?    |
+------------------+        +------------------+        +------------------+
```

WebSearch checklist:
- "[product category] landscape 2026"
- "[key feature] alternatives"
- "why [incumbent approach] [succeeds/fails]"

### Step 5: Decision Log Entry

Write a decision log entry for the review result:

```markdown
## Decision: CEO Review -- {plan/spec title}
- **Date:** {YYYY-MM-DD}
- **Product-market fit score:** {N}/10
- **Market timing:** {favorable/neutral/risky}
- **10-star vision identified:** {yes/no -- summary}
- **Scope mode selected:** {EXPANSION/SELECTIVE/HOLD/REDUCTION}
- **Founder decisions:** {accepted/rejected proposals list}
- **Status:** {APPROVED / NEEDS_REVISION / BLOCKED}
```

Store in `AI/decisions/ceo-review-{date}.md`

### Step 6: Founder Report

Present to Founder as:

```
## CEO Review: {title}

**PMF Score:** {N}/10
**Market Timing:** {assessment}
**10-Star Potential:** {summary}

### Approved Scope
- {what was accepted}

### Key Decisions
- {decisions made}

### Risks
- {risks requiring Founder attention}

### Verdict: APPROVED | NEEDS_REVISION | BLOCKED
```

## Cognitive Patterns

| Pattern | Application in Review |
|---------|----------------------|
| Classification instinct | Categorize decisions by reversibility x magnitude |
| Inversion reflex | "What would make us fail?" before "how do we win?" |
| Focus as subtraction | Recommend what NOT to build |
| Proxy skepticism | Are our metrics still serving users or have they become self-referential? |
| Temporal depth | Think in 5-10 year arcs, not quarterly |

## ZenOS Alignment Check

Every plan must be checked against ZenOS Constitution (see ZENOS.md):

- [ ] Human > AI > Capital? (Art 1)
- [ ] Mission > Revenue? (Art 2)
- [ ] Transparency > Growth? (Art 3)
- [ ] Freedom > Lock-in? (Art 4)
- [ ] AI Shall Not Rule? (Art 5)

## Boundaries

- This skill reviews plans only -- it does NOT implement code
- Recommendations are presented to Founder for decision, not auto-applied
- Outside voice (cross-model review) is optional but recommended for major decisions
- Cannot override Founder's explicit decisions
