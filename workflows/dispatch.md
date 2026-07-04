---
name: dispatch-pipeline
description: "Auto-dispatch 25 /idea files by Inverted Triangle layer with Binh Phap strategy gates"
trigger: "/dispatch --project <name>"
owner: COO
agents: [founder, ceo, cfo, cto, cmo, cso, coo, chro]
layers:
  - name: L1
    binh_phap: dao
    owner: Founder
    files: [00-framework.md, 01-agency-os.md, 04-refactor-frame.md]
  - name: L5
    binh_phap: thien
    owners: [CSO, CMO]
    files: [05→14 (10 files)]
  - name: L4
    binh_phap: dia
    owner: CTO
    files: [spec from L5]
  - name: L2
    binh_phap: tuong
    owners: [CEO, CFO]
    files: [02, 16, 17, 19, 22, 23 (6 files)]
  - name: L3
    binh_phap: phap
    owners: [COO, CHRO]
    files: [03, 15, 18, 20, 21, 24 (6 files)]
---

# Dispatch Workflow — Binh Phap Auto-Sequence

## Gate Protocol

```yaml
gate_protocol:
  name: "WIN-WIN-WIN"
  questions:
    - "Founder: Có win không? (Mission alignment?)"
    - "Platform: Hệ thống có win không? (System integrity?)"
    - "Khách hàng: Họ có win không? (Customer value?)"
  pass: "Cả 3 YES → TIẾN"
  fail: "Any NO → DỪNG LẠI → report reason → fix → retry gate"
```

## Sequence Diagram

```
READY ──► GATE 1: ĐẠO (L1 Founder)
             │
             ▼
         WIN-WIN-WIN?
          ├── YES ──► GATE 2: THIÊN (L5 CSO/CMO)
          └── NO  ──► STOP
                         │
                         ▼
                     WIN-WIN-WIN?
                      ├── YES ──► GATE 3: ĐỊA (L4 CTO)
                      └── NO  ──► DEFENSE
                                     │
                                     ▼
                                 WIN-WIN-WIN?
                                  ├── YES ──► GATE 4: TƯỚNG (L2 CEO/CFO)
                                  └── NO  ──► ADJUST
                                                 │
                                                 ▼
                                             WIN-WIN-WIN?
                                              ├── YES ──► GATE 5: PHÁP (L3 COO/CHRO)
                                              └── NO  ──► ANTI-DILUTION
                                                             │
                                                             ▼
                                                         WIN-WIN-WIN?
                                                          ├── YES ──► COMPLETED
                                                          └── NO  ──► MOVEMENT ADJUST
```

## Status Propagation

| Status | Meaning |
|--------|---------|
| `pending` | Chưa dispatch layer này |
| `in_progress` | Layer đang được dispatch |
| `gate_pending` | Chờ WIN-WIN-WIN approval |
| `passed` | Layer hoàn thành, gate OK |
| `failed` | Gate failed — dừng lại |
| `completed` | All 5 layers done |

## Layer Details

### Gate 1 — ĐẠO (L1 Founder)
**Mission First.** Founder đọc 00-framework.md, 01-agency-os.md, 04-refactor-frame.md.
Xác nhận mission alignment. Nếu mission sai → không làm gì cả.

**Trigger:** Chapter 1 (Strategy Assessment)

### Gate 2 — THIÊN (L5 Mặt Trận)
**Market Timing.** CSO/CMO đọc 10 files về market + brand + sales.
Phân tích thị trường. Nếu thời cơ sai → lui về phòng thủ.

**Trigger:** Chapter 3 (Tactics) + Chapter 13 (Intelligence)

### Gate 3 — ĐỊA (L4 Sản Xuất)
**Position Building.** CTO nhận spec từ L5.
Xây vị thế sản phẩm, phòng thủ cạnh tranh.

**Trigger:** Chapter 4 (Position) + Chapter 10 (Terrain)

### Gate 4 — TƯỚNG (L2 Chiến Lược)
**Command & Resources.** CEO/CFO đọc 6 files về strategy + finance.
Phân bổ nguồn lực, xác định hướng đi.

**Trigger:** Chapter 1 (Strategy) + Chapter 6 (Flexibility)

### Gate 5 — PHÁP (L3 Vận Hành)
**Process & Automation.** COO/CHRO đọc 6 files về ops + people.
Chuẩn hóa quy trình, setup OKRs, tự động hóa.

**Trigger:** Chapter 2 (Operations) + Chapter 9 (Movement)

## Completion

Khi cả 5 gates pass:
```json
{
  "distribution_state": {
    "status": "completed",
    "completed_layers": ["L1", "L5", "L4", "L2", "L3"],
    "dispatched_agents": [
      "founder-agent", "cso-agent", "cmo-agent",
      "cto-agent", "ceo-agent", "cfo-agent",
      "coo-agent", "chro-agent"
    ],
    "gates_passed": ["L1", "L5", "L4", "L2", "L3"]
  }
}
```

**Next:** Ready for `mekong first-ship` or layer-specific commands.
