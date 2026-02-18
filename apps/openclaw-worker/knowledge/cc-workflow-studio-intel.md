# 🎨 CC Workflow Studio — 始計篇 Visual Strategy Designer

> Source: github.com/breaking-brake/cc-wf-studio
> Assessed: 2026-02-18 | Status: NOTE — P3 future
> Action: Theo dõi, xem xét khi cần visual workflow

## What
- VSCode Extension: visual drag-and-drop workflow editor
- Design multi-agent workflows with conditional branching
- Export → .claude/commands/ or .gemini/skills/ (slash commands)
- AI-assisted editing (natural language → workflow)
- MCP server integration

## Concerns
- ⚠️ AGPL-3.0 license = restrictive cho commercial use
- VSCode-only = Tôm Hùm chạy terminal, không dùng VSCode
- "Usage Examples: Coming soon" = chưa mature
- 121 releases nhưng thiếu docs

## Potential Use Case
- Chủ Tịch vẽ workflow → export .md → CTO pick up
- Visual strategy planning thay cho text-based /plan:hard
- Phù hợp hơn cho RaaS clients (non-technical)

## Skip Reason (for now)
- /plan:hard + ClaudeKit commands đủ mạnh
- Terminal-first workflow > VSCode plugin
- AGPL license cần review kỹ
