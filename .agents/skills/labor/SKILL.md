---
name: labor
description: Vietnamese Labor Code 2019 compliance, foreign work permits, overtime caps & safety regulations.
---

# Vietnamese Labor Code & Foreign Worker Compliance Engine (`mekong labor`)

Autonomous compliance engine for the Vietnamese Labor Code 2019 (Law No. 45/2019/QH14), Foreign Work Permit & Exemption regulations (Decree 152/2020/ND-CP & Decree 70/2023/ND-CP), Overtime Caps & Tiered Pay calculation (Articles 98 & 107), Severance / Job Loss Allowance (Articles 46 & 47), and Internal Labor Regulations (Nội quy Lao động - Article 118).

## Core Capabilities

1. **Foreign Work Permit & Statutory Exemption Evaluation (Decree 152/2020/ND-CP & Decree 70/2023/ND-CP)**:
   - Evaluates foreign employee eligibility across roles: `EXPERT`, `EXECUTIVE`, `MANAGER`, `TECHNICAL_WORKER`.
   - Checks statutory work permit exemptions: capital contribution $\ge 3$ billion VND (LLC owner / Board member), WTO 11 service sector internal transfer, or married to a Vietnamese citizen.
   - Generates statutory application dossiers and required paperwork checklists (Form 11/PLI, health check, criminal record, qualifications).
2. **Tiered Overtime & Night Shift Pay Calculation (Labor Code 2019, Article 98)**:
   - Calculates statutory overtime pay rates:
     - Normal working day overtime: **150%**
     - Weekly rest day overtime: **200%**
     - Public holidays & paid leave overtime: **300%**
     - Night shift work surcharge (22:00 - 06:00): +**30%** base
     - Overtime at night surcharge: +**20%** daytime rate
   - Computes total compensation, gross overtime pay, and blended hourly multipliers.
3. **Statutory Overtime Caps & Safety Monitoring (Labor Code 2019, Article 107)**:
   - Monitors monthly cap: $\le 40$ hours/month.
   - Monitors standard annual cap: $\le 200$ hours/year.
   - Validates exceptional annual cap eligibility: $\le 300$ hours/year (garment, footwear, electronics, seasonal agriculture, continuous shift operations) with required prior notification to the Department of Labor, Invalids and Social Affairs (DOLISA).
4. **Severance Pay & Job Loss Allowance (Articles 46 & 47)**:
   - Calculates Severance Pay (Trợ cấp thôi việc - Article 46): 0.5 month salary per qualifying year of service (excluding time covered by statutory Unemployment Insurance BHTN).
   - Calculates Job Loss Allowance (Trợ cấp mất việc làm - Article 47): 1.0 month salary per qualifying year, guaranteed minimum of 2.0 months salary.
5. **Internal Labor Regulations (Nội quy Lao động - Article 118)**:
   - Mandatory registration for enterprises with $\ge 10$ employees.
   - Validates 8 statutory required chapters: working hours & rest, order at workplace, occupational safety & health, prevention of sexual harassment, protection of enterprise assets, disciplinary violations & sanctions, material liability, persons authorized to discipline.
   - Persistent SQLite WAL storage at `.mekong/labor.db`.

## CLI Usage

```bash
# System overview and labor compliance telemetry
mekong labor
mekong labor status --json

# Assess foreign work permit vs exemption
mekong labor permit "John Smith" "United States" "EXPERT" --deg "Master of Computer Science" --exp 5 --capital 0 --json
mekong labor permit "David Miller" "United Kingdom" "EXECUTIVE" --capital 3500000000 --json

# Calculate statutory overtime pay (Article 98)
mekong labor overtime 150000 --weekday 10 --weekend 6 --night 4 --json

# Audit overtime caps against statutory limits (Article 107)
mekong labor caps "EMP-001" "Nguyễn Văn Hùng" 35 180 --industry "ELECTRONICS" --exceptional --json

# Calculate severance or job loss allowance (Articles 46 & 47)
mekong labor severance "Trần Thị Mai" 20000000 6.0 --bhtn 4.5 --type SEVERANCE --json
mekong labor severance "Lê Hoàng Nam" 25000000 5.0 --bhtn 3.0 --type JOB_LOSS --json

# Audit Internal Labor Regulations (NQLD - Article 118)
mekong labor regulations 45 --registered --json
mekong labor regulations 15 --registered=false --missing "SEXUAL_HARASSMENT" --json

# List applications or employees
mekong labor list --type permits --json
mekong labor list --type overtime --json
```

## Native MCP Tools

- `mekong_labor_permit`: Assess foreign worker eligibility for work permit or statutory exemption under Decree 152/2020 & 70/2023.
- `mekong_labor_overtime`: Calculate statutory overtime pay and night shift rates under Labor Code 2019 Article 98.
- `mekong_labor_caps`: Audit monthly and annual overtime working hours against Article 107 statutory limits.
- `mekong_labor_severance`: Calculate statutory severance pay (Article 46) or job loss allowance (Article 47).
- `mekong_labor_regulations`: Audit Internal Labor Regulations (NQLD) compliance under Article 118 for enterprises $\ge 10$ employees.
- `mekong_labor_list`: Query registered work permit dossiers and employee overtime records.
- `mekong_labor_status`: Retrieve Vietnamese labor compliance engine metrics, telemetry, and statutory threshold status.
