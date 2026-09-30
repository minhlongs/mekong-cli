---
name: prosecution
description: Vietnamese People's Procuracy, Public Prosecution & Judicial Supervision Suite.
---

# `mekong prosecution` — Vietnamese People's Procuracy & Public Prosecution Suite

Governed by:
- **Law on Organization of the People's Procuracies 2014 (Law No. 63/2014/QH13 — Luật Tổ chức Viện kiểm sát nhân dân 2014)**: Defines functions, tasks, powers, organization, and procurator ranks for public prosecution and judicial supervision.
- **Criminal Procedure Code 2015 (Law No. 101/2015/QH13 — Bộ luật Tố tụng hình sự 2015)** as amended by Law No. 02/2021/QH15: Governs crime report resolution (Điều 144-150), investigation supervision, procedural approvals (arrests, detentions, searches), indictments (Điều 243-244), and trial prosecution.
- **Law on Execution of Criminal Judgments 2019 (Law No. 41/2019/QH14 — Luật Thi hành án hình sự 2019)**: Supervision of temporary custody, temporary detention, prison administration, and sentence execution.
- **Civil Procedure Code 2015 & Law on Administrative Procedures 2015**: Supervision of civil, marriage/family, commercial, and administrative dispute resolution.

---

## 1. Capabilities & Core Subcommands

| Subcommand | Description | Key Parameters |
|---|---|---|
| `mekong prosecution` | Executive dashboard overview of Procurators, Crime Reports, Cases, Indictments & Inspections | `--json` |
| `mekong prosecution procurator` | Register a Procurator (Kiểm sát viên) under Law 63/2014/QH13 | `--id`, `--name`, `--rank <SO_CAP\|TRUNG_CAP\|CAO_CAP\|TOI_CAO>`, `--level`, `--unit`, `--decision`, `--status`, `--json` |
| `mekong prosecution report` | Record and supervise receipt of crime reports and denunciations (Điều 144-150) | `--id`, `--source`, `--summary`, `--group`, `--procuracy`, `--procurator`, `--status`, `--deadline-days`, `--json` |
| `mekong prosecution case` | Record criminal case investigation supervision, arrest & detention approvals | `--id`, `--name`, `--agency`, `--procurator`, `--article`, `--stage`, `--warrants`, `--detentions`, `--demands`, `--json` |
| `mekong prosecution indictment` | Issue formal prosecutorial indictment (Cáo trạng truy tố - Điều 243-244) | `--id`, `--case-id`, `--defendant`, `--offense`, `--clause`, `--procuracy`, `--procurator`, `--decision`, `--issue-date`, `--json` |
| `mekong prosecution inspection` | Record custody inspection of detention facility or prison under Law THAHS 2019 | `--id`, `--facility`, `--procuracy`, `--procurator`, `--checked`, `--violations`, `--protest/--no-protest`, `--compliance`, `--date`, `--json` |
| `mekong prosecution list` | List records across procurators, reports, cases, indictments, and inspections | `--category <procurators\|reports\|cases\|indictments\|inspections\|all>`, `--limit <int>`, `--json` |
| `mekong prosecution status` | Aggregate operational telemetry metrics | `--json` |

---

## 2. MCP Tools Reference

The suite exposes 7 canonical MCP tools with dual-engine parity across FastMCP and JSON-RPC 2.0 stdio:

- `mekong_prosecution_procurator`: Register procurator under Law 63/2014/QH13.
- `mekong_prosecution_report`: Record and supervise crime report resolution under Articles 144-150 BLTTHS 2015.
- `mekong_prosecution_case`: Record investigation supervision and arrest/detention procedural approvals.
- `mekong_prosecution_indictment`: Issue prosecutorial indictment under Articles 243-244 BLTTHS 2015.
- `mekong_prosecution_inspection`: Record detention facility or prison custody inspection.
- `mekong_prosecution_list`: Query records across categories.
- `mekong_prosecution_status`: Aggregate operational telemetry.
