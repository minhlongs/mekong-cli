# Plan: OpenClaw Skills Harvest V2

**Date:** 2026-02-20
**Status:** Draft
**Priority:** HIGH
**Binh Pháp:** 法篇 — ClawHub 5,705 raw → Awesome 3,002 curated → Official 164 hand-picked

---

## Tổng Quan

Harvest top skills từ 3 nguồn OpenClaw ecosystem, sử dụng ClawHub CLI v0.7.0 (`npx clawhub@latest`) để install. Hiện có 66 skills, target thêm 15-25 skills chất lượng cao.

## Phases

| # | Phase | Status | Link |
|---|-------|--------|------|
| 1 | Audit & Dedup hiện tại | Pending | [phase-01](phase-01-audit-dedup.md) |
| 2 | P0 Install — Must Have | Pending | [phase-02](phase-02-p0-install.md) |
| 3 | P1 Install — High Value | Pending | [phase-03](phase-03-p1-install.md) |
| 4 | P2 Browse — Awesome List | Pending | [phase-04](phase-04-p2-awesome-browse.md) |
| 5 | Security Gate — VirusTotal | Pending | [phase-05](phase-05-security-gate.md) |
| 6 | CỬU ĐỊA Matrix Mapping | Pending | [phase-06](phase-06-cuu-dia-matrix.md) |
| 7 | Test Top 5 | Pending | [phase-07](phase-07-test-top-5.md) |
| 8 | Document & Registry Update | Pending | [phase-08](phase-08-document.md) |

## Research Findings

### Sources Verified ✅
| Source | URL | Stats | Verified |
|--------|-----|-------|----------|
| Official | `github.com/openclaw/skills` | 1,169⭐ 405🍴 | ✅ Real |
| Awesome | `github.com/VoltAgent/awesome-openclaw-skills` | 16,955⭐ 1,718🍴 | ✅ Real |
| ClawHub CLI | `npx clawhub@latest` | v0.7.0 | ✅ Working |
| Registry | `clawdhub.com` | 5,705 skills | ✅ Live |

### Current State
- 66 active skills in `.claude/skills/`
- Previous harvest (2026-02-18): 5 skills installed
- `skill-seekers` v3.0.0 available (scrapes docs → skills)
- `clawhub` CLI available via npx (NOT locally installed)

### Key Tools
- `npx clawhub@latest install <slug>` — Install skill
- `npx clawhub@latest search "<query>"` — Vector search
- `npx clawhub@latest explore` — Browse latest
- `npx clawhub@latest inspect <slug>` — Preview before install
- `npx clawhub@latest list` — Show installed (from lockfile)

## Dependencies
- Node.js + npx (✅ available)
- Internet access for ClawHub registry
- `.claude/skills/` write access
