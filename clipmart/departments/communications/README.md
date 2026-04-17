# Communications Department as a Service

> Replace a PR/comms manager with AI agents that draft press releases, internal announcements, board minutes, and external communications.

## Value Proposition

| What you replace | Annual cost | What you pay |
|-----------------|-------------|--------------|
| Comms Manager ($100k) | $100,000/yr | $49/mo floor |
| PR Agency retainer | $60,000/yr | $6/piece |
| **Total replaced** | **$160,000/yr** | **~$1,200/yr** |

## What This Department Does

1. **Press Releases** — Product launches, funding announcements, partnerships
2. **Internal Communications** — All-hands content, org announcements, team updates
3. **Board Minutes** — Meeting summaries, action items, resolution documentation
4. **Crisis Communications** — Rapid response briefs, holding statements, media Q&A
5. **Executive Communications** — CEO LinkedIn posts, thought leadership drafts

## Outcome-Based Pricing

| Deliverable | Price |
|------------|-------|
| Press release drafted | $20 |
| Internal announcement | $8 |
| Board minutes | $15 |
| Crisis comms brief | $30 |
| Executive thought leadership post | $15 |
| All-hands content | $20 |

**Monthly floor:** $49.

## Included Commands

```bash
mekong board-minutes    # Board meeting minutes
mekong board-report     # Board communications pack
mekong business-report  # Business communications report
```

## Install

```bash
mekong install dept-communications
```

## Configuration

```bash
# .mekong/.env.dept-communications
DEPT_COMMS_CEO_NAME="Founder Name"
DEPT_COMMS_COMPANY_NAME="Your Company"
DEPT_COMMS_BRAND_VOICE=bold,transparent,founder-led
DEPT_COMMS_PRESS_CONTACT=press@yourcompany.com
DEPT_COMMS_INTERNAL_CHANNEL=slack  # slack|email|notion
DEPT_COMMS_MEDIA_TARGETS=techcrunch,venturebeat,producthunt
```

## Comparison

| Metric | PR Agency | Communications Dept SaS |
|--------|-----------|------------------------|
| Monthly retainer | $5,000-15,000 | $49 floor |
| Press release | $500-2,000 | $20 |
| Turnaround | 3-5 days | 2-4 hours |
| Internal comms | Not included | Included |
| Crisis response | Business hours | 24/7 |
