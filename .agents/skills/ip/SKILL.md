---
name: ip
description: Intellectual Property (IP), Trademark (SHTT), Nice Classification, Patents, Software Copyright, and official NOIP fee calculation.
---

# /ip — Intellectual Property (IP), Trademark, Patent & Copyright Engine

Autonomous Vietnamese Intellectual Property & Industrial Property management conforming to:
- **Luật Sở hữu trí tuệ 2005 (sửa đổi, bổ sung 2022 — Luật số 07/2022/QH15)**.
- **Thỏa ước Nice phiên bản 12-2024 (Nice Classification)** phân loại hàng hóa và dịch vụ quốc tế.
- **Nghị định 65/2023/NĐ-CP**: Quy định chi tiết một số điều và biện pháp thi hành Luật SHTT về sở hữu công nghiệp.
- **Nghị định 17/2023/NĐ-CP**: Hướng dẫn thi hành Luật SHTT về quyền tác giả, quyền liên quan tác phẩm phần mềm máy tính.
- **Thông tư 263/2016/TT-BTC**: Biểu mức thu phí, lệ phí sở hữu công nghiệp tại Cục Sở hữu trí tuệ (IP VIETNAM - NOIP).

## Architecture

```
mekong ip
     │
     ├── (overview)         ── IP portfolio metrics, active marks, patents & copyrights
     ├── trademark          ── Register trademark application with Nice classification
     ├── search             ── Phonetical & orthographical trademark conflict & confusion search
     ├── patent             ── Synthesize statutory patent specification & claims (Art. 102)
     ├── copyright          ── Generate software computer program copyright dossier (Decree 17/2023)
     ├── fees               ── Itemize official state filing & examination fees (TT 263/2016)
     ├── list               ── Query historical IP portfolio records
     └── status             ── IP engine telemetry in .mekong/ip.db
```

## CLI Usage

```bash
// turbo
mekong ip [OPTIONS]
```

### Subcommands

| Command | Arguments / Flags | Description |
|---------|-------------------|-------------|
| `mekong ip` | `[--json]` | Overview IP portfolio dashboard, registered marks, patents, copyrights |
| `mekong ip trademark` | `<name> [--class 09] [--applicant NAME] [--spec S] [--json]` | Register trademark application under Nice Classification |
| `mekong ip search` | `<name> [--class 09] [--json]` | Search trademark similarity and likelihood of confusion risk |
| `mekong ip patent` | `<title> <field> [--applicant NAME] [--claims N] [--json]` | Draft statutory patent specification & claims |
| `mekong ip copyright`| `<software> <author> [--version 1.0.0] [--json]` | Synthesize software copyright registration dossier |
| `mekong ip fees` | `[--tm-classes N] [--pat-claims M] [--copyrights K] [--json]` | Calculate official state IP fees under Circular 263/2016/TT-BTC |
| `mekong ip list` | `[--limit N] [--json]` | List registered trademarks, patents, and software copyrights |
| `mekong ip status` | `[--json]` | IP engine status, supported Nice classes, and SQLite database |

## MCP Tools Integration

- `mekong_ip_trademark(mark_name, nice_class="09", applicant_name="", goods_services_spec="")`: Register trademark.
- `mekong_ip_search(mark_name, nice_class="09")`: Search phonetical & orthographical trademark conflicts.
- `mekong_ip_patent(title, technical_field, applicant_name="", independent_claims=1, dependent_claims=2)`: Draft patent specification.
- `mekong_ip_copyright(software_name, author_name, version="1.0.0", repository_url="", lines_of_code=10000)`: Compile software copyright dossier.
- `mekong_ip_fees(trademark_classes=1, patent_claims=1, software_copyrights=1)`: Calculate official fees.
- `mekong_ip_status()`: Retrieve IP engine metrics and status.
