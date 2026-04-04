# Mekong Company OS — OpenClaw Meta-Skill

> "I am OpenClaw. I run this company." — Mekong CLI v6.0

## Overview

Mekong Company OS is an AI-operated business platform exposing **342+ commands** across **22 departments** organized into **6 operational layers** derived from 孫子兵法 (Sun Tzu's Art of War).

Each department maps to a ClawHub-publishable skill package. All commands dispatch through the `mekong` engine via CC CLI.

## Activation

```bash
# Install all departments
claw install mekong-company-os

# Install specific department
claw install mekong/finance
claw install mekong/sales
claw install mekong/engineering

# Use a command
mekong finance-monthly-close Q1-2026
mekong sales-pipeline-build "B2B SaaS"
mekong cook "add user authentication"
```

## The 6 Layers

| Layer | Art of War Chapter | Role | Commands |
|-------|--------------------|------|----------|
| Studio | 孫子兵法 — Complete | VC Studio / Venture Builder | 23 |
| Founder | 始計 — Initial Calculations | Founder / CEO | 52 |
| Business | 作戰 — Waging War | Business Lead / GTM | 71 |
| Product | 謀攻 — Attack by Stratagem | Product Manager / Designer | 31 |
| Engineering | 軍爭 — Military Contention | Engineer / Tech Lead | 66 |
| Ops | 九變 — Nine Variations | DevOps / Platform | 41 |

## The 22 Departments

| Department | Layer | Key Commands |
|------------|-------|--------------|
| `finance` | business | finance-monthly-close, finance-budget-plan, finance-collections |
| `sales` | business | sales-pipeline-build, sales-deal-close, sdr-prospect |
| `marketing` | business | marketing-campaign-run, writer-blog, growth-experiment |
| `hr` | business | hr-recruit, hr-onboard, people-onboard |
| `legal` | business | legal-contract-review, compliance-soc2-prep |
| `engineering` | engineering | cook, code, fix, test, deploy, review |
| `devops` | ops | devops-deploy-pipeline, sre-morning-check, platform-monitoring-setup |
| `data` | engineering | data-ingest, data-transform, ml-experiment |
| `security` | ops | sec-audit, iam-provision, sec-incident-response |
| `product` | product | product-discovery, product-sprint-plan, pm-roadmap |
| `ops` | ops | ops-health-sweep, ops-security-audit, incident-postmortem |
| `business` | business | business-revenue-engine, business-quarterly-review |
| `founder` | founder | founder-validate, founder-raise, founder-ipo |
| `studio` | studio | studio-bootstrap, dealflow-source, expert-match |
| `ipo` | founder | ipo-readiness-check, ir-metrics, ir-roadshow |
| `corpdev` | founder | corpdev-scout, corpdev-evaluate, corpdev-integrate |
| `intl` | business | intl-market-assess, intl-localize, intl-entity |
| `esg` | ops | esg-report, esg-carbon, esg-dei |
| `risk` | ops | risk-assess, risk-monitor, risk-fraud-detect |
| `audit` | ops | audit-plan, audit-sox, audit-itgc |
| `board` | founder | board-manage, board-minutes, board-compliance |
| `intel` | studio | intel-asymmetry, terrain-position, momentum-velocity |

## Architecture

```
mekong-cli (shell wrapper)
  └── CC CLI (engine)
        └── .claude/commands/*.md (342+ commands)
              └── factory/contracts/*.json (410 machine contracts)
                    └── mekong/agents/ (specialized agents)
```

## Universal LLM Config

```bash
export LLM_BASE_URL=https://openrouter.ai/api/v1
export LLM_API_KEY=sk-or-v1-yourkey
export LLM_MODEL=anthropic/claude-sonnet-4
```

Supports: Anthropic, OpenAI, Google, Qwen, DeepSeek, Ollama, OpenRouter.

## License

BSL-1.1 — Business Source License. Free for individual use. Commercial license required for SaaS products built on this OS.

See: [manifest.json](manifest.json) for full command mapping.
