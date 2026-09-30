---
name: adminlaw
description: Vietnamese Legal Normative Documents, Regulatory Impact Assessment (RIA) & State Compensation Liability Suite.
---

# `mekong adminlaw` — Vietnamese Legal Normative Documents, RIA & State Compensation Liability Suite

Governed by:
- **Law on Promulgation of Legal Normative Documents 2015 (Law No. 80/2015/QH13, amended by Law No. 63/2020/QH14)**: Defines legal document hierarchy (Điều 4: Luật, Nghị quyết QH, Pháp lệnh UBTVQH, Nghị định Chính phủ, Quyết định TTg, Thông tư Bộ trưởng, Nghị quyết HĐND, Quyết định UBND), drafting procedures, appraisal, and mandatory Regulatory Impact Assessment (RIA - Đánh giá tác động chính sách tại Điều 35 & 58).
- **Law on State Compensation Liability 2017 (Luật Trách nhiệm bồi thường của Nhà nước - Law No. 10/2017/QH14)**: Regulates State compensation liability to individuals and organizations suffering damage caused by public duty performers in administrative management, criminal proceedings, civil/administrative litigation, and judgment enforcement; settlement procedures, advance payouts, and official reimbursement (trách nhiệm hoàn trả).
- **Decree No. 34/2016/NĐ-CP & Decree No. 154/2020/NĐ-CP**: Detailed implementation guidelines on formulation and appraisal of legal normative documents.
- **Decree No. 68/2018/NĐ-CP**: Detailed provisions on settlement procedures, reimbursement obligations, and allocation of State Budget compensation funds.

---

## 1. Capabilities & Core Subcommands

| Subcommand | Description | Key Parameters |
|---|---|---|
| `mekong adminlaw` | Executive dashboard overview of Legal Documents, RIA Appraisals, Compensation Claims & Reimbursements | `--json` |
| `mekong adminlaw document` | Register or update Vietnamese legal normative document under Article 4 Law No. 80/2015/QH13 | `--number`, `--title`, `--type`, `--body`, `--promulgation`, `--effective`, `--status`, `--json` |
| `mekong adminlaw ria` | Conduct Regulatory Impact Assessment (RIA) & legality appraisal under Articles 35 & 58 | `--code`, `--doc-number`, `--economic`, `--social`, `--burden`, `--agency`, `--verdict`, `--date`, `--notes`, `--json` |
| `mekong adminlaw claim` | File State Compensation liability claim dossier under Articles 2 & 41-43 Law No. 10/2017/QH14 | `--code`, `--name`, `--citizen-id`, `--sphere`, `--agency`, `--amount`, `--date`, `--status`, `--json` |
| `mekong adminlaw settle` | Issue State Compensation settlement decision under Articles 45-48 Law No. 10/2017/QH14 | `--code`, `--claim-code`, `--material`, `--mental`, `--date`, `--status`, `--json` |
| `mekong adminlaw reimburse` | Order at-fault state officer reimbursement to State Budget under Articles 64-67 Law No. 10/2017/QH14 | `--code`, `--decision-code`, `--officer`, `--fault-degree`, `--amount`, `--status`, `--json` |
| `mekong adminlaw list` | List records across legal documents, RIA appraisals, claims, settlements, and reimbursements | `--category <documents\|ria\|claims\|settlements\|reimbursements>`, `--limit <int>`, `--json` |
| `mekong adminlaw status` | Display Administrative Law & State Compensation operational telemetry | `--json` |

---

## 2. MCP Tools Reference

The suite exposes 7 canonical MCP tools with dual-engine parity across FastMCP and JSON-RPC 2.0 stdio:

- `mekong_adminlaw_document`: Register or update Vietnamese legal normative document.
- `mekong_adminlaw_ria`: Conduct Regulatory Impact Assessment (RIA) & legality appraisal.
- `mekong_adminlaw_claim`: File or update State Compensation liability claim dossier.
- `mekong_adminlaw_settle`: Issue State Compensation damage settlement decision.
- `mekong_adminlaw_reimburse`: Order at-fault public officer reimbursement to State Budget.
- `mekong_adminlaw_list`: Query administrative law records across categories.
- `mekong_adminlaw_status`: Aggregate administrative law, RIA appraisal, and state compensation telemetry.
