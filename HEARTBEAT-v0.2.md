# HEARTBEAT.md — Autonomous Task Checklist
# mekong-cli reads this file every {interval} minutes and executes pending items.
# Mark items [x] when done. Agent will skip completed items.

## Every 30 minutes
- [ ] Check SLA-at-risk tickets → notify if any approaching deadline
- [ ] Check for new support emails → create tickets if found

## Every morning (8:00 AM)
- [ ] Generate daily standup report
- [ ] Check overdue invoices → queue reminder emails
- [ ] List leads needing follow-up today
- [ ] Show today's calendar events

## Every Monday (10:00 AM)
- [ ] Run payment follow-up SOP for overdue invoices
- [ ] Review leads in pipeline > 14 days without activity

## Every Sunday (6:00 PM)
- [ ] Generate weekly business digest
- [ ] Calculate weekly MRR change
- [ ] Send weekly summary to owner

## Monthly (1st of month, 9:00 AM)
- [ ] Run monthly financial close for previous month
- [ ] Generate monthly report
- [ ] Check recurring expenses for any changes
- [ ] Review customer health scores

## On Demand (triggered by events)
- [ ] New payment received → update invoice status, record revenue
- [ ] New ticket created → auto-triage
- [ ] Lead score > 70 → alert owner for follow-up
- [ ] Budget usage > 80% → warn owner
