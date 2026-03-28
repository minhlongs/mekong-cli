---
description: "Developer command suite — audit, debug, deploy, design, PR review, refactor, scaffold, review."
---

# /dev — Developer Command Suite

**AUTO-EXECUTE MODE.** Detect sub-command from user prompt and execute.

## Available Sub-Commands

### `/dev audit` — Code Audit
1. Scan codebase for quality issues
2. Check dependencies for vulnerabilities
3. Review code patterns and anti-patterns
4. Report with severity ratings

### `/dev debug` — Debug Issues
1. Read error logs / stack traces
2. Reproduce the issue
3. Trace root cause
4. Apply fix → verify

### `/dev deploy` — Deploy Code
1. Run pre-deploy checks (lint, test, build)
2. Execute deployment
3. Verify deployment success

### `/dev design` — Design Implementation
1. Translate design specs to code
2. Create components following design system
3. Verify visual accuracy

### `/dev pr-review` — Pull Request Review
1. Read the diff
2. Check for: security issues, bugs, performance, readability
3. Suggest improvements
4. Approve or request changes

### `/dev refactor` — Code Refactoring
1. Identify refactoring target
2. Understand current behavior
3. Apply refactoring (preserving behavior)
4. Run tests to verify no regression

### `/dev scaffold` — Scaffold New Module
1. Create directory structure
2. Generate boilerplate files
3. Setup configs (linting, testing)
4. Add to project build system

### `/dev review` — General Code Review
1. Read specified code
2. Analyze quality, correctness, security
3. Provide actionable feedback

## Engineering Commands

### `/eng sprint-execute` — Sprint Execution
1. Read current sprint plan
2. Execute top-priority tasks
3. Update progress

### `/eng tech-debt` — Tech Debt Sprint
1. Identify tech debt items
2. Prioritize by impact
3. Execute fixes
4. Measure improvement

### `/eng onboard-dev` — Onboard Developer
1. Generate project overview
2. Environment setup guide
3. Architecture walkthrough
4. First task assignment

### `/engineering new-service` — Create New Service
1. Service template selection
2. Scaffold codebase
3. Configure CI/CD
4. Documentation

### `/engineering refactor` — Large Refactoring
1. Impact analysis
2. Phased refactoring plan
3. Execute with tests
4. Migration guide

## Backend & Frontend

### `/backend api-build` — Build API Endpoint
1. Define API contract (OpenAPI/REST)
2. Implement handler
3. Add validation
4. Write tests

### `/backend db-task` — Database Task
1. Schema design/migration
2. Write migration files
3. Update ORM models
4. Test data integrity

### `/frontend ui-build` — Build UI Component
1. Component implementation
2. Styling (CSS/design system)
3. Responsive layout
4. Accessibility check

### `/frontend responsive-fix` — Fix Responsive Issues
1. Identify breakpoint issues
2. Fix layout/styling
3. Test across screen sizes

## Worker Commands (quick tasks)

| Command | Action |
|---------|--------|
| `/worker code` | Quick code task |
| `/worker build` | Build project |
| `/worker test` | Run tests |
| `/worker commit` | Stage & commit |
| `/worker push` | Push to remote |
| `/worker scan` | Security scan |
| `/worker health` | Health check |
| `/worker exec` | Execute command |
| `/worker log` | View logs |
| `/worker trace` | Trace execution |
| `/worker rollback` | Rollback changes |
| `/worker backup` | Backup project |

## DevOps Commands

### `/devops deploy-pipeline` — Setup Deploy Pipeline
1. CI/CD configuration
2. Build steps definition
3. Deploy automation
4. Monitoring setup

### `/devops rollback` — Rollback Deployment
1. Identify rollback target
2. Execute rollback
3. Verify system state

## Release Commands

### `/release ship` — Ship Release
1. Version bump
2. Changelog generation
3. Build production bundle
4. Tag and push

### `/release hotfix` — Ship Hotfix
1. Create hotfix branch
2. Apply fix
3. Test
4. Cherry-pick to main

### `/releng pre-release` — Pre-Release Checklist
1. Feature freeze verification
2. Integration tests
3. Performance benchmarks
4. Documentation update

### `/releng post-release` — Post-Release
1. Verify production
2. Monitor metrics
3. Update status pages
4. Send release notes
