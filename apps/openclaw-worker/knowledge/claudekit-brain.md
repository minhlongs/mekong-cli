# ClaudeKit Brain — CTO Command Routing Intelligence

> Source: https://docs.claudekit.cc/llms.txt (Feb 2026)
> CTO/CC CLI/Antigravity dùng file này để chọn ClaudeKit command đúng theo task type.

## 🎯 COMMAND ROUTING MAP (CTO PHẢI THUỘC)

| Task Type | ClaudeKit Command | Khi nào dùng |
|:----------|:-----------------|:-------------|
| Build feature | `/cook "task" --auto` | Default cho mọi task |
| Build + parallel | `/cook "task" --parallel --auto` | 3+ features hoặc complex |
| Bug fix (1 bug) | `/debug "issue"` | Root cause → fix |
| Bug fix (2+ bugs) | `/fix "issues" --parallel --auto` | Multi-bug parallel |
| Root cause analysis | `/debug "tại sao..."` | Investigation |
| Strategic/architecture | `/plan:parallel "task"` | Redesign, migration |
| Deep planning | `/plan:hard "task"` | Complex planning + research |
| Quick planning | `/plan:fast "task"` | Simple planning |
| CI failure | `/plan:ci` | CI/CD broken |
| CRO optimize | `/plan:cro` | Conversion rate |
| Bootstrap project | `/bootstrap:auto:parallel` | New project parallel |
| Code review | `/review:codebase` | Quality audit |
| Parallel review | `/review:codebase:parallel` | Multi-reviewer audit |
| Search codebase | `/scout "pattern"` | File discovery |
| Test | `/test` | Run tests |
| UI test | `/test:ui` | Visual test |
| Git commit | `/check-and-commit` hoặc `/git` | Commit + push |

## 🤖 AGENT ROSTER (14 Engineer + 13 Marketing)

### Engineer Agents
planner, fullstack-developer, debugger, tester, code-reviewer, docs-manager, project-manager, journal-writer, git-manager, ui-ux-designer, brainstormer, researcher, mcp-manager, scout

### Marketing Agents (nếu cần)
campaign-manager, seo-specialist, copywriter, content-creator, email-wizard, social-media-manager, analytics-analyst, funnel-architect, lead-qualifier, attraction-specialist, sales-enabler, community-manager, continuity-specialist

## 🧩 TOP SKILLS CHO CTO

| Skill | Mục đích |
|:------|:---------|
| cook | End-to-end implementation |
| debug | Root cause analysis |
| fix | Bug fixing (--parallel cho multi-bug) |
| scout | Fast codebase search |
| gkg | Semantic code graph |
| context-engineering | Monitor context, optimize tokens |
| sequential-thinking | Complex problem solving |
| problem-solving | 5 techniques for stuck situations |
| ai-multimodal | Process audio/video/images |
| better-auth | Authentication patterns |
| web-testing | Playwright + Vitest + k6 |
| repomix | Package repo for AI |

## ⚡ ORCHESTRATION RULES

1. **Sequential** (default): planner → fullstack-dev → tester → code-reviewer → git-manager
2. **Parallel**: researcher×N → Aggregate → planner (cho 3+ features)
3. **Hybrid**: Mix sequential + parallel
4. **Handoff**: Via shared files (plans/, docs/) + TodoWrite
5. **Đa luồng = BÊN TRONG CC CLI** (Task tool), KHÔNG spawn nhiều tmux panes
6. **1 tmux pane + --parallel flag** = cách đúng

## 🔧 TOOLS

- **CCS (Claude Code Switch)**: Switch accounts to avoid rate limits
- **Kanban**: Visual dashboard `/kanban plans/`
- **MCP**: `/use-mcp` delegate to Gemini CLI to save context

## 📝 WORKFLOW PATTERNS

```
Feature: /plan:hard → /cook --parallel --auto → /test → /review → /git
Bug:     /debug → /fix --parallel --auto → /test → /git
New App:  /bootstrap:auto:parallel → /test:ui → /review:codebase:parallel
CI Fix:   /plan:ci → /fix --auto → /test → /git
```
