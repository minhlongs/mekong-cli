# Phase 4: P2 Browse — Awesome List Categories

**Priority:** MEDIUM | **Status:** Pending

## Awesome List Categories Phù Hợp Mekong-CLI

Từ 31 categories (3,002 skills), chọn 13 relevant nhất:

| Category | Count | Relevance | Action |
|----------|-------|-----------|--------|
| AI & LLMs | 287 | ⭐⭐⭐⭐⭐ | Browse top 20 |
| Search & Research | 253 | ⭐⭐⭐⭐⭐ | Browse top 15 |
| DevOps & Cloud | 212 | ⭐⭐⭐⭐ | Browse top 10 |
| Web & Frontend Development | 202 | ⭐⭐⭐⭐ | Browse top 10 |
| Marketing & Sales | 143 | ⭐⭐⭐⭐ | Browse top 10 |
| Browser & Automation | 139 | ⭐⭐⭐ | Browse top 5 |
| Productivity & Tasks | 135 | ⭐⭐⭐ | Browse top 5 |
| Coding Agents & IDEs | 133 | ⭐⭐⭐⭐⭐ | Browse top 20 |
| CLI Utilities | 129 | ⭐⭐⭐ | Browse top 5 |
| Clawdbot Tools | 120 | ⭐⭐⭐⭐ | Browse top 10 |
| Git & GitHub | 66 | ⭐⭐⭐ | Browse top 5 |
| Security & Passwords | 64 | ⭐⭐⭐⭐ | Browse top 5 |
| Agent-to-Agent Protocols | 18 | ⭐⭐⭐⭐⭐ | Browse ALL |

## Steps

1. **Fetch Awesome list README** (đã có từ research)
2. **Filter** mỗi category theo relevance
3. **`clawhub inspect`** top candidates
4. **Select** max 10 thêm từ P2 round
5. **Install** selected skills

## Browse Command
```bash
# Search by category keyword
npx clawhub@latest search "agent to agent protocol" --no-input
npx clawhub@latest search "coding agent IDE" --no-input
npx clawhub@latest search "task productivity" --no-input
```

## Selection Criteria
- Không trùng chức năng skills hiện tại
- VirusTotal clean
- Có >10 stars trên ClawHub hoặc trong Awesome curated list
- SKILL.md < 500 lines (lightweight)
