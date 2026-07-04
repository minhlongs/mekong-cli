# Email + Lifecycle Sequences

> Automated email flows to onboard, nurture, convert, and retain Mekong CLI users.

---

## 1. Onboarding (Day 0-7 after install)

| Day | Email | Trigger |
|-----|-------|---------|
| 0 | **Welcome to Mekong CLI** -- Overview of what Mekong does, link to docs, your personal dashboard URL. | `mekong install` completes |
| 1 | **Your First Agent Workflow** -- Step-by-step walkthrough: `mekong run` with a template workflow. Links to quickstart guide. | 24h after install |
| 3 | **Agent Configuration Deep Dive** -- How to configure agents, set API keys, define custom prompts. Link to `mekong config` reference. | 72h after install |
| 7 | **Your First Full Pipeline** -- Combine multiple agents into a pipeline. Example: research -> spec -> code -> review. | 7d after install |

Copy: `mekong blueprint email:onboarding --output ./emails/`

---

## 2. Nurture (Weekly)

| Day | Email | Purpose |
|-----|-------|---------|
| Thu | **This Week in Mekong** -- New features shipped, community workflows, upcoming roadmap items. | Awareness + engagement |
| Thu | **Use Case Spotlight** -- Deep-dive into one real-world workflow (e.g., "How team X uses Mekong for PR review"). | Education |
| Thu | **Community Highlight** -- Top community workflow of the week, contributor shoutout, GitHub star milestone. | Social proof |

Serviced by: `mekong blueprint email:nurture --list`

---

## 3. Trial Conversion (Day 10-14)

| Day | Email | Trigger |
|-----|-------|---------|
| 10 | **Your Trial Ends in 3 Days** -- Usage summary (workflows run, time saved). CTA: upgrade to Pro. | Trial end -3d |
| 12 | **Case Studies** -- 3 customer stories showing ROI: solo dev, small team, agency. Each with metrics. | Trial end -1d |
| 14 | **Pricing Comparison** -- Free vs Pro vs Enterprise side-by-side. Feature breakdown + annual discount. | Trial ends today |

Copy: `mekong blueprint email:trial-conversion --output ./emails/`

---

## 4. Win-back (30 days after churn)

| Day | Email | Purpose |
|-----|-------|---------|
| 30 | **What You Missed** -- Feature releases since you left, community growth stats, performance improvements. | Re-engagement |
| 32 | **Special Offer** -- 30% off first 3 months of Pro. Limited to 7 days. CTA: restore your workspaces. | Conversion |
| 37 | **Last Chance** -- Offer expires in 48 hours. Reminder of your past workflows and saved configs. | Urgency |

Trigger: `mekong blueprint email:winback --target churned`

---

## Implementation Notes

- All emails use `mekong email send --template <name> --to <user>` under the hood.
- Templates live in `~/.mekong/emails/` and are plain Markdown with `{{ variable }}` interpolation.
- Track opens with a 1x1 transparent pixel; track clicks with `mekong link` redirects.
- Bounce handling: auto-remove email on 3 consecutive hard bounces.
- Unsubscribe: one-click `[Unsubscribe]({{unsubscribe_url}})` in every footer.
- A/B test subject lines on nurture emails starting week 4.
