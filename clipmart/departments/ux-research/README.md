# UX Research Department as a Service

> Replace a $180/hr UX researcher with AI agents. User interviews synthesized in hours, not weeks.

## Value Proposition

| What you replace | Annual cost | What you pay |
|-----------------|-------------|--------------|
| UX Researcher contract | $86,400/yr | $49/mo floor |
| UserTesting platform | $12,000/yr | Included |
| **Total replaced** | **$98,400/yr** | **~$1,200/yr** |

## What This Department Does

1. **Interview Synthesis** — Transcripts → themes → insights → recommendations
2. **Usability Testing** — Test plan, screener, moderation guide, findings report
3. **UX Audits** — Heuristic evaluation, accessibility, copy clarity
4. **Survey Design** — NPS, CSAT, feature validation surveys
5. **Design Recommendations** — Prioritized UX fixes with effort/impact matrix

## Outcome-Based Pricing

| Deliverable | Price |
|------------|-------|
| Usability test plan + script | $20 |
| Interview synthesis (5 users) | $25 |
| UX audit report | $35 |
| Design recommendations doc | $18 |
| Survey design + analysis | $15 |

**Monthly floor:** $49.

## Included Commands

```bash
mekong ux-interview    # Interview guide + synthesis
mekong ux-usability    # Usability test planning + analysis
```

## Install

```bash
mekong install dept-ux-research
```

## Configuration

```bash
# .mekong/.env.dept-ux-research
DEPT_UX_DESIGN_TOOL=figma
DEPT_UX_FIGMA_TOKEN=your_token
DEPT_UX_RECORDING_TOOL=loom  # loom|zoom|otter
DEPT_UX_RESEARCH_REPO=notion  # Where findings are stored
```
