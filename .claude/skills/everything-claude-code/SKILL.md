---
name: Everything Claude Code (ECC)
description: Tích hợp ECC patterns — AgentShield security scans, continuous learning hooks (wins.jsonl), và skill-creator. Binh Pháp Ch.3 Mưu Công.
---

# Everything Claude Code (ECC) 🛡️ (Mưu Công)
Patterns tổng hợp từ everything-claude-code architecture, được inject vào workflow ClaudeKit.

## AgentShield Security
Trước mỗi `/cook` hoặc `/check-and-commit`:
1. Scan for hardcoded secrets (API keys, tokens, passwords)
2. Check for dangerous patterns: `eval()`, `exec()`, `rm -rf`
3. Validate file permissions changes
4. Flag suspicious network calls

## Continuous Learning
Sau mỗi mission hoàn thành:
1. Ghi nhận thành công vào `wins.jsonl`
2. Ghi nhận thất bại vào `lessons.md`
3. Pattern extraction cho next mission

## Skill Creator (Native)
Thay thế HyperSkill Generator. Sử dụng `skill-creator` agent từ ClaudeKit v2.9.1 để tự động sinh SKILL.md files.

_Binh Pháp: 謀攻 MƯU CÔNG — 上兵伐謀 (Thượng sách là phạt mưu). ECC = hệ thống phòng thủ trí tuệ._
