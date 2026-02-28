# Phase 3: P1 Install — High Value

**Priority:** HIGH | **Status:** Pending

## Target Skills (10)

### Coding & DevOps
| Skill | Lý do |
|-------|-------|
| `deploy-agent` | C.R.A.B Deploy Agent — automated deployment |
| `gcloud` | Google Cloud Platform operations |
| `agent-orchestrator` | General agent orchestration |
| `executing-plans` | Execute implementation plans systematically |

### Marketing & Business
| Skill | Lý do |
|-------|-------|
| `marketing-strategy-pmm` | Product marketing strategy |
| `competitive-intelligence-market-research` | Market research |
| `content-writing-thought-leadership` | Content creation |
| `social-media-management` | Social media ops |

### Security & Quality
| Skill | Lý do |
|-------|-------|
| `openclaw-security-audit` | OpenClaw-specific security checks |
| `agent-security-auditor` | Agent-level security review |

## Install Commands
```bash
# Install P1 batch
for skill in deploy-agent gcloud agent-orchestrator executing-plans \
  marketing-strategy-pmm competitive-intelligence-market-research \
  content-writing-thought-leadership social-media-management \
  openclaw-security-audit agent-security-auditor; do
  echo "Installing: $skill"
  npx clawhub@latest install "$skill" --dir .claude/skills --no-input
done
```

## Verification
- [ ] Mỗi skill có SKILL.md hợp lệ
- [ ] Không trùng chức năng với skills hiện tại
- [ ] VirusTotal check cho mỗi skill
