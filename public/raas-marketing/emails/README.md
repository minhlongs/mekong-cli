# RaaS Email Templates

Mustache email templates for RaaS onboarding sequence.

## Templates

| # | Template | Trigger | Goal |
|---|----------|---------|------|
| 01 | `01-welcome.mustache` | Immediate | Dashboard login |
| 02 | `02-day3-quick-win.mustache` | Day 3 | First agent deployed |
| 03 | `03-day7-social-proof.mustache` | Day 7 | Upgrade consideration |
| 04 | `04-day14-transformation.mustache` | Day 14 | Tier upgrade |
| 05 | `05-day30-winback.mustache` | Day 30 (inactive) | Re-activation |
| 06 | `06-day45-feature-spotlight.mustache` | Day 45 | Feature adoption |

## Variables

All templates use Mustache syntax `{{variable}}`.

### User Variables
- `{{name}}` — Recipient name
- `{{email}}` — Recipient email
- `{{company}}` — Company name
- `{{tier}}` — Subscription tier

### URL Variables
- `{{dashboard_url}}` — Login/dashboard link
- `{{browse_agents_url}}` — Agent marketplace
- `{{calendar_url}}` — Booking calendar
- `{{upgrade_url}}` — Upgrade page
- `{{choose_tier_url}}` — Tier selection
- `{{book_session_url}}` — Strategy call booking
- `{{activate_trial_url}}` — Trial activation
- `{{learn_webhooks_url}}` — Webhook docs
- `{{api_docs_url}}` — API documentation

### Metrics Variables
- `{{agents_used}}` — Number of agents user deployed
- `{{agents_limit}}` — Tier agent limit
- `{{agents_running}}` — Currently active agents
- `{{agents_deployed}}` — Total deployed
- `{{roi_amount}}` / `{{roi_tracked}}` — ROI dollar amount
- `{{hours_saved}}` — Hours saved per week
- `{{workflow_count}}` — Number of automations

### Sender Variables
- `{{sender_name}}` — Sender name
- `{{tier_limit}}` — Tier-specific limit

## Usage

### With Node.js
```js
const Mustache = require('mustache');
const fs = require('fs');

const template = fs.readFileSync('./01-welcome.mustache', 'utf8');
const view = {
  name: 'John',
  dashboard_url: 'https://app.agencyos.network/dashboard',
  sender_name: 'RaaS Team',
  tier_limit: '5 agents'
};

const output = Mustache.render(template, view);
```

### With Python
```python
from mustache import render

with open('./01-welcome.mustache') as f:
    template = f.read()

view = {
    'name': 'John',
    'dashboard_url': 'https://app.agencyos.network/dashboard',
    'sender_name': 'RaaS Team',
    'tier_limit': '5 agents'
}

output = render(template, **view)
```

## Configuration

See `email-config.json` for:
- Send schedules and triggers
- Target metrics (open rate, CTR, conversion)
- Segmentation rules
- A/B test variants

## Segmentation

| Segment | Trigger | Behavior |
|---------|---------|----------|
| Active | Daily login | Skip Day 7 upgrade push |
| Stuck | 0 agents by Day 3 | Send onboarding call offer |
| Power User | 3+ agents | Fast-track to Premium |
| At-Risk | No login after Day 5 | Trigger win-back early |

## Source

Generated from: `docs/raas/email-sequences/onboarding-sequence.md`
