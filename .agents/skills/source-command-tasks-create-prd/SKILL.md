---
name: "source-command-tasks-create-prd"
description: "Create Product Requirement Document"
---

# source-command-tasks-create-prd

Use this skill when the user asks to run the migrated source command `tasks-create-prd`.

## Command Template

// turbo

# /create-prd - PRD Generator

Generate comprehensive Product Requirement Document.

## Usage

```
/create-prd [product-name]
```

## Codex Prompt Template

```
PRD Generation workflow:

Create PRD with sections:

# {Product Name} - PRD

## Overview
- Problem statement
- Solution summary
- Target users

## Goals & Success Metrics
- Primary goals
- KPIs
- Success criteria

## User Stories
- As a {user}, I want to {action}, so that {benefit}

## Requirements
### Functional Requirements
- FR1: {requirement}

### Non-Functional Requirements
- Performance: {spec}
- Security: {spec}
- Scalability: {spec}

## Technical Approach
- Architecture
- Tech stack
- Integrations

## Timeline
- Phase 1: {scope} - {duration}
- Phase 2: {scope} - {duration}

## Risks & Mitigations
- Risk 1: {description} → Mitigation: {approach}

Save to: docs/prd/{product}.md
```

## Example Output

```
📋 PRD Created: Client Portal

Sections:
- Overview ✅
- Goals (3 defined) ✅
- User Stories (8) ✅
- Requirements (15 FR, 5 NFR) ✅
- Timeline (3 phases) ✅

📁 Saved: docs/prd/client-portal.md
```
