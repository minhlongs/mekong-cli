# Phase 2: P0 Install — Must Have

**Priority:** CRITICAL | **Status:** Pending

## Target Skills (5)

| Skill | Source | Lý do | Search Score |
|-------|--------|-------|--------------|
| `ec-task-orchestrator` | openclaw/skills | Multi-agent task orchestration, missing từ harvest v1 | 3.448 |
| `joko-orchestrator` | openclaw/skills | Deterministic autonomous planning, coordination | 3.486 |
| `security-audit` | openclaw/skills | Security auditing codebase | 3.614 |
| `cloudflare-manager` | openclaw/skills | Cloudflare Workers ops (raas-gateway) | 0.953 |
| `piv` | openclaw/skills | Plan-Implement-Validate pattern (matches core DNA) | 0.911 |

## Install Commands
```bash
# Install P0 batch — one by one to verify each
npx clawhub@latest install ec-task-orchestrator --dir .claude/skills --no-input
npx clawhub@latest install joko-orchestrator --dir .claude/skills --no-input
npx clawhub@latest install security-audit --dir .claude/skills --no-input
npx clawhub@latest install cloudflare-manager --dir .claude/skills --no-input
npx clawhub@latest install piv --dir .claude/skills --no-input
```

## Verification
- [ ] Mỗi skill có SKILL.md
- [ ] Đọc SKILL.md verify nội dung hợp lý
- [ ] Không conflict với skills hiện tại
- [ ] Check VirusTotal report trên ClawHub page

## Security Check
Trước khi install mỗi skill:
```bash
npx clawhub@latest inspect <slug> --no-input  # Review metadata + files
```
