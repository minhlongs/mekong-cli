---
name: procuracy
description: Vietnamese People's Procuracy, Public Prosecution & Judicial Supervision Suite.
---

# `mekong procuracy` — Vietnamese People's Procuracy, Public Prosecution & Judicial Supervision Suite

Governed by:
- **Law on Organization of the People's Procuracies 2014 (Luật Tổ chức Viện kiểm sát nhân dân - Law No. 63/2014/QH13)**: Regulates the functions, duties, and powers of the People's Procuracies in exercising the power of public prosecution (quyền công tố) and supervising judicial activities (kiểm sát hoạt động tư pháp); organizational system (VKSNDTC, VKSND cấp cao, VKSND cấp tỉnh, VKSND cấp huyện, Viện kiểm sát quân sự); and ranks of Procurators (Kiểm sát viên các ngạch tại Điều 74).
- **Criminal Procedure Code 2015 (Luật Tố tụng hình sự 2015, amended 2021)**: Regulates public prosecution, prosecution approval of arrests/searches, issuing indictments (Cáo trạng truy tố tại Điều 243), maintaining prosecution in court, and judicial supervision.
- **Law on Temporary Detention and Custody 2015 (Luật Thi hành tạm giữ, tạm giam 2015)**: Regulates procuracy supervision over the legality of arrest, custody, detention facilities, and release of persons detained unlawfully or past detention terms (Điều 22-26).
- **Civil Procedure Code 2015 & Law on Administrative Litigation 2015**: Appellate, cassation, and reopening protests (Kháng nghị phúc thẩm, giám đốc thẩm, tái thẩm tại Điều 27-31).

---

## 1. Capabilities & Core Subcommands

| Subcommand | Description | Key Parameters |
|---|---|---|
| `mekong procuracy` | Executive dashboard overview of Prosecutors, Indictments, Detention Supervisions & Judicial Protests | `--json` |
| `mekong procuracy prosecutor` | Register or update a Procurator (Kiểm sát viên) under Article 74 Law on Organization of People's Procuracies | `--badge`, `--name`, `--rank`, `--level`, `--office`, `--date`, `--status`, `--json` |
| `mekong procuracy indictment` | Issue or track a criminal prosecution indictment under Article 243 Criminal Procedure Code | `--number`, `--case`, `--accused`, `--article`, `--prosecutor`, `--court`, `--date`, `--status`, `--json` |
| `mekong procuracy detention` | Supervise legality of arrest, custody, and temporary detention under Articles 22-26 | `--code`, `--facility`, `--detainee`, `--measure`, `--start`, `--end`, `--inspector`, `--status`, `--date`, `--notes`, `--json` |
| `mekong procuracy protest` | Issue an appellate, cassation, or reopening protest against court judgment under Articles 27-31 | `--code`, `--judgment`, `--court`, `--type`, `--ground`, `--prosecutor`, `--date`, `--status`, `--json` |
| `mekong procuracy list` | List records across prosecutors, indictments, detention supervisions, and protests | `--category <prosecutors\|indictments\|detentions\|protests>`, `--limit <int>`, `--json` |
| `mekong procuracy status` | Display People's Procuracy & Public Prosecution telemetry status | `--json` |

---

## 2. MCP Tools Reference

The suite exposes 6 canonical MCP tools with dual-engine parity across FastMCP and JSON-RPC 2.0 stdio:

- `mekong_procuracy_prosecutor`: Register or update Procurator (Kiểm sát viên).
- `mekong_procuracy_indictment`: Issue or track criminal prosecution indictment (Cáo trạng).
- `mekong_procuracy_detention`: Supervise legality of arrest, custody, and temporary detention.
- `mekong_procuracy_protest`: File judicial protest (Kháng nghị) against court judgments.
- `mekong_procuracy_list`: Query People's Procuracy records across categories.
- `mekong_procuracy_status`: Aggregate public prosecution and judicial supervision telemetry.
