---
name: audit
description: Enterprise SOX 404, ITGC, and COSO internal controls audit execution, testing, and compliance reporting.
---

# /audit — Enterprise SOX 404 & ITGC Internal Controls Audit Engine

Providing deterministic automated internal controls testing, compliance scoring, audit trail evidence generation, and deficiency remediation across 4 core ITGC / SOX 404 domains (Access Controls, Change Management, Computer Operations, and Software Development).

## Internal Controls Frameworks & Domains

1. **Khung Quy Chuẩn Áp Dụng**:
   - **Sarbanes-Oxley Section 404 (SOX 404)**: Kiểm soát nội bộ đối với lập báo cáo tài chính (ICFR).
   - **COSO Internal Control — Integrated Framework (2013)**.
   - **IT General Controls (ITGC)**: Chuẩn mực kiểm toán hệ thống thông tin.
2. **4 Miền Kiểm Soát Cốt Lõi (Core Domains)**:
   - **AC (Access Controls & IAM)**: Phân quyền nhiệm vụ (SoD), cổng phê duyệt rủi ro cao (CEO Override), rà soát đặc quyền.
   - **CM (Change Management)**: Kiểm soát pre-push hook tự động, commit chuẩn conventional, năng lực rollback tức thời.
   - **CO (Computer Operations)**: Tính toàn vẹn CSDL (SQLite WAL), sức khỏe hệ thống và nhật ký vận hành.
   - **SD (System Development & Security)**: Bất biến import thuần standard-library ở core, quét sạch credentials/secret.
3. **Phân Loại Khiếm Khuyết & Ý Kiến Kiểm Toán**:
   - **Unqualified / Effective (≥ 90%)**: Không có khiếm khuyết trọng yếu (No material weaknesses).
   - **Qualified (70% - 89%)**: Có tồn tại khiếm khuyết đáng lưu ý nhưng hệ thống cơ bản vận hành hữu hiệu.
   - **Adverse (< 70%)**: Tồn tại khiếm khuyết trọng yếu (Material weaknesses) cần khắc phục khẩn cấp.

## Architecture

```
mekong audit
     │
     ├── (overview)         ── Executive compliance posture, score, and opinion
     ├── run                ── Execute deterministic internal controls test battery
     ├── controls           ── Browse internal control matrix and testing procedures
     ├── findings           ── Track open deficiencies and remediation plans
     └── status             ── Audit system telemetry and database metrics
```

## CLI Usage

```bash
// turbo
mekong audit [OPTIONS]
```

### Options & Subcommands

| Command | Arguments / Flags | Description |
|---------|-------------------|-------------|
| `mekong audit` | `[--json]` | Overview dashboard with latest compliance score and audit opinion. |
| `mekong audit run` | `[--framework all\|sox\|itgc] [--json]` | Run automated test battery across internal controls catalog. |
| `mekong audit controls` | `[--domain AC\|CM\|CO\|SD\|all] [--framework all\|sox\|itgc] [--json]` | Query internal controls catalog and risk levels. |
| `mekong audit findings` | `[--severity all\|critical\|high\|medium\|low] [--json]` | Inspect open audit deficiencies and remediation plans. |
| `mekong audit status` | `[--json]` | Database records and audit telemetry in `.mekong/audit.db`. |

## Native MCP Tools

| MCP Tool Name | Arguments | Description |
|---------------|-----------|-------------|
| `mekong_audit_run` | `framework` | Execute automated SOX/ITGC controls audit procedures. |
| `mekong_audit_controls` | `domain, framework` | Browse internal control matrix and test procedures. |
| `mekong_audit_findings` | `min_severity` | Query open audit deficiencies and corrective action plans. |
| `mekong_audit_status` | *(none)* | Retrieve audit system health and latest compliance score. |
