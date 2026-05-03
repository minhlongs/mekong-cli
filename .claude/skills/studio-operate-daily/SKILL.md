---
name: studio-operate-daily
description: Daily studio operations and workflow management for AgencyOS projects
---

# Studio Operate Daily

## Purpose
Manages daily studio operations including project health checks, task prioritization, and workflow automation.

## Usage
- Run daily health checks on active projects
- Prioritize and route tasks to appropriate agents
- Monitor build/test/deploy status across the monorepo
- Generate daily status reports

## Commands
- Check project health: `npm run build && npm test`
- Review pending tasks in `plans/` directory
- Scan for blocking issues across apps/

## Constraints
- Do NOT run git commit/push — CI/CD gate handles that
- Fix at most 5 files per mission
- Follow Binh Pháp routing rules for task assignment
