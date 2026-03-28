---
description: "Context, docs, and task commands — prime context, create PRD, TODO management, documentation."
---

# /context — Context, Docs & Tasks Command Suite

**AUTO-EXECUTE MODE.** Detect sub-command from user prompt and execute.

## Context Commands

### `/prime` — Quick Context Prime
Fast project context loading:

// turbo
```bash
echo "⚡ Quick Prime"
echo "=============="
if [ -f "README.md" ]; then echo "📄 README found"; head -20 README.md; fi
echo ""
echo "📁 Project structure:"
find . -maxdepth 2 -not -path '*/node_modules/*' -not -path '*/.git/*' -not -path '*/__pycache__/*' | head -30
echo ""
if [ -f "package.json" ]; then
  echo "📦 Package: $(cat package.json | grep -m1 '"name"' | sed 's/.*: "//;s/".*//')"
  echo "🔧 Scripts: $(cat package.json | grep -A20 '"scripts"' | grep ':' | head -5)"
fi
if [ -f "pyproject.toml" ]; then
  echo "🐍 Python project detected"
  head -10 pyproject.toml
fi
```

### `/context prime` — Full Context Prime
Deep context loading:
1. Project structure (tree -L 3)
2. README.md overview
3. Config files (package.json, pyproject.toml, etc.)
4. Architecture overview
5. Key dependencies list
6. Entry points identification

### `/agency prime` — Agency Context Prime
Load full agency/business context:
1. Business model overview
2. Current projects status
3. Team structure
4. Revenue state

## Documentation Commands

### `/docs create` — Create Documentation
1. Auto-detect project type
2. Generate docs structure
3. Create README if missing
4. API documentation
5. Setup guide

### `/docs changelog` — Add Changelog
1. Read git log since last tag
2. Categorize changes (features, fixes, breaking)
3. Generate CHANGELOG.md entry

## Task Commands

### `/create-prd` — Create PRD (Product Requirement Document)
Generate comprehensive PRD with:
1. Overview (problem, solution, target users)
2. Goals & Success Metrics (KPIs)
3. User Stories (As a ... I want ... So that ...)
4. Requirements (Functional + Non-Functional)
5. Technical Approach (architecture, stack)
6. Timeline (phased)
7. Risks & Mitigations
8. Save to: `docs/prd/{product}.md`

### `/todo` — TODO Management
1. Scan codebase for TODO/FIXME comments
2. Prioritize by age and location
3. Create actionable task list

## Utility Commands

### `/utils mermaid` — Generate Mermaid Diagrams
Create mermaid diagrams from code/architecture

### `/utils refactor` — Guided Refactoring
Step-by-step refactoring with safety checks

### `/utils search` — Codebase Search
Semantic search across the codebase
