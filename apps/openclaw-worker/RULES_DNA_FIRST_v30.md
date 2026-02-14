# RULE TÔM HÙM v30 — DNA-First Resource Allocation

> **第六篇 虛實 (Xu Shi)** — Tập trung binh lực vào DNA, vệ tinh bảo trì
>
> "20% vệ tinh → 80% DNA khi vệ tinh 100/100"

---

## Nguyên tắc

1. **DNA Project** = `mekong-cli/AgencyOS` (engine, api, landing, raas-gateway, worker) — dự án sinh tiền RaaS
2. **Satellite Projects** = client projects (sophia, wellnexus, apex-os, 84tea, anima119, com-anh-duong) — doanh thu dịch vụ

## Thuật toán phân bổ

### Phase 1: Satellite Sprint (ban đầu)

- **Ưu tiên 100%** vệ tinh cho đến khi tất cả đạt 100/100 Binh Pháp
- Mục tiêu: bàn giao khách nhanh nhất

### Phase 2: DNA-First (sau khi vệ tinh 100/100)

- **80% tasks** → DNA (mekong-cli core: engine, api, landing, raas-gateway)
- **20% tasks** → Satellite maintenance (kiểm tra regression, i18n sync)
- Cơ chế: mỗi 5 task, 4 task DNA + 1 task satellite

### Phase 3: Rebalance (nếu satellite regress)

- Nếu bất kỳ satellite nào drop dưới 100/100 → tạm chuyển 1 pane cho satellite
- Khi fix xong → quay lại Phase 2

## Config

```javascript
DNA_PROJECTS: ['engine', 'api', 'agencyos-landing', 'agencyos-web', 'raas-gateway'];
SATELLITE_PROJECTS: ['sophia-ai-factory', 'wellnexus', 'apex-os', '84tea', 'anima119', 'com-anh-duong-10x'];
DNA_PRIORITY_RATIO: 0.8; // 80% DNA khi satellites 100/100
```

## State tracking

```json
{
  "completedTasks": { "84tea": [...], "engine": [...] },
  "satelliteReadiness": { "84tea": 9, "sophia-ai-factory": 9, ... },
  "phase": "satellite_sprint" | "dna_first" | "rebalance",
  "dnaTaskCounter": 0,
  "totalTaskCounter": 0
}
```
