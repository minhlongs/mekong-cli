---
name: police
description: Vietnamese People's Public Security & Grassroots Security Forces Suite.
---

# `mekong police` — Vietnamese People's Public Security & Grassroots Security Forces Suite

Governed by:
- **Law on People's Public Security 2018 (Law No. 37/2018/QH14 — Luật Công an nhân dân 2018)** as amended by Law No. 21/2023/QH15.
- **Law on Forces Participating in Safeguarding Security and Order at the Grassroots Level 2023 (Law No. 30/2023/QH15 — Luật Lực lượng tham gia bảo vệ an ninh, trật tự ở cơ sở 2023)**.
- **Decree No. 40/2024/NĐ-CP**: Detailed provisions and operational guidelines for grassroots security teams.
- **Circular No. 14/2024/TT-BCA**: Operational procedures, equipment, and incident reporting for grassroots security personnel.
- **Law on Residence 2020 (Law No. 68/2020/QH15 — Luật Cư trú)**: Administrative residence verification, stay notifications, and household inspection.

---

## 1. Capabilities & Core Subcommands

| Subcommand | Description | Key Parameters |
|---|---|---|
| `mekong police` | Executive dashboard overview of officers, grassroots teams, and incidents | `--json` |
| `mekong police officer` | Register an officer of the People's Public Security | `--badge`, `--name`, `--rank`, `--position`, `--unit`, `--spec`, `--status`, `--json` |
| `mekong police team` | Register a grassroots security team (Tổ bảo vệ ANTT ở cơ sở) | `--id`, `--name`, `--ward`, `--district`, `--city`, `--leader`, `--members`, `--gear`, `--status`, `--json` |
| `mekong police incident` | Report a public security or social order incident | `--id`, `--type`, `--location`, `--ward`, `--reporter`, `--unit`, `--severity`, `--status`, `--date`, `--json` |
| `mekong police patrol` | Log a joint security patrol mission | `--id`, `--type`, `--route`, `--badge`, `--team`, `--start`, `--end`, `--checked`, `--infractions`, `--json` |
| `mekong police residence` | Record an administrative household residence and stay inspection | `--id`, `--address`, `--head`, `--badge`, `--registered`, `--present`, `--temp-stay/--no-temp-stay`, `--violating`, `--date`, `--compliance`, `--json` |
| `mekong police list` | List records across officers, teams, incidents, patrols, and residence | `--type <officers\|teams\|incidents\|patrols\|residence\|all>`, `--limit <int>`, `--json` |
| `mekong police status` | Aggregate operational telemetry metrics | `--json` |

---

## 2. MCP Tools Reference

The suite exposes 7 canonical MCP tools with dual-engine parity across FastMCP and JSON-RPC 2.0 stdio:

- `mekong_police_officer`: Register police officer under Law 37/2018/QH14.
- `mekong_police_team`: Register grassroots security team under Law 30/2023/QH15.
- `mekong_police_incident`: Report and triage security incident.
- `mekong_police_patrol`: Log joint security patrol mission under Circular 14/2024/TT-BCA.
- `mekong_police_residence`: Record household residence check under Law on Residence 2020.
- `mekong_police_list`: Query records across categories.
- `mekong_police_status`: Aggregate operational telemetry.
