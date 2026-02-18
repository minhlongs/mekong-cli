# 🦞 TÔM HÙM — Vòng Lặp Giám Sát Vô Tận

> **始計:** Kích hoạt vòng lặp giám sát vô tận, tối ưu từng node nhỏ, chỉ `/cook` khi thật sự cần.

## Hiện Trạng (v1)

```
scan (build/lint/test) → fix (/cook) → verify → next project → loop
```

**Vấn đề:**
- Chỉ phát hiện build error, lint error, test failure
- Không đánh giá ROI trước khi cook
- Không check deploy config, missing features, UI/UX, SEO
- Không ưu tiên task nào quan trọng hơn

## Thiết Kế Mới (v2) — 始計→謀攻→軍形 Nâng Cao

```
┌─────────────────────────────────────────────────────────┐
│  VÒNG LẶP VÔ TẬN (mỗi 60s)                           │
│                                                         │
│  ① 始計 DEEP SCAN                                      │
│     ├─ build / lint / test (như cũ)                     │
│     ├─ deploy config check (vercel.json, wrangler.toml) │
│     ├─ env check (.env.example vs .env)                 │
│     ├─ SEO check (meta tags, sitemap)                   │
│     ├─ dependency audit (npm audit --json)              │
│     └─ production readiness score (0-100)               │
│                                                         │
│  ② 謀攻 PLAN (đánh giá ROI)                            │
│     ├─ Classify: critical / high / medium / low         │
│     ├─ Estimate tokens needed                           │
│     ├─ Check daily token budget (作戰)                  │
│     └─ Decision: COOK or DEFER                          │
│                                                         │
│  ③ 軍形 COOK (chỉ khi ROI > threshold)                 │
│     ├─ /cook critical issues first                      │
│     ├─ Max 1 mission per cycle                          │
│     └─ Log token usage per mission                      │
│                                                         │
│  ④ 軍形 VERIFY → loop back to ①                        │
└─────────────────────────────────────────────────────────┘
```

## Node Scan Checklist (từng project)

| Node | Check | Severity |
|:-----|:------|:---------|
| Build | `npm run build` exit code | critical |
| Lint | `npm run lint` errors | high |
| Test | `npm test` failures | high |
| Deploy | `vercel.json` / `wrangler.toml` exists | critical |
| Env | `.env.example` variables vs `.env` | critical |
| SEO | `<title>`, `<meta>`, sitemap.xml | medium |
| Deps | `npm audit --json` high/critical | high |
| TypeScript | `tsc --noEmit` strict errors | medium |
| i18n | Missing translation keys | low |
| Score | Production readiness 0-100 | summary |

## ROI Decision Matrix

```
                    Token Cost
                    LOW (<500)    HIGH (>2000)
Impact  CRITICAL    ✅ COOK NOW   ✅ COOK NOW
        HIGH        ✅ COOK NOW   ⚠️ PLAN FIRST
        MEDIUM      ✅ COOK NOW   ❌ DEFER
        LOW         ❌ DEFER      ❌ DEFER
```

## Config Changes

### [MODIFY] config.js
```javascript
PROJECTS: ['84tea', 'anima119', 'agencyos-web', 'agencyos-landing'],
SCAN_DEPTH: 'deep',  // 'shallow' = build only, 'deep' = full checklist
COOK_THRESHOLD: 'high',  // minimum severity to auto-cook
```

### [MODIFY] auto-cto-pilot.js
- Add `deepScan()` alongside existing `scanProject()`
- Add `assessROI(error)` → returns { cook: boolean, reason: string }
- Add production readiness scorer
- Integrate with token-tracker daily budget

## Implementation Priority

1. **GIÓ (15min):** Add deploy config + env check to scanner
2. **RỪNG (30min):** Add ROI classifier + token budget gate
3. **LỬA (1hr):** Add production readiness scorer
4. **NÚI (2hr):** Full deep scan with SEO/deps/i18n

## Binh Pháp Mapping

| Nguyên tắc | Hán | Implementation |
|:-----------|:----|:---------------|
| Trinh sát trước | 始計 | Deep scan toàn diện |
| Không đánh khi chưa biết | 知己知彼 | ROI assessment trước khi cook |
| Quân quý thắng nhanh | 兵貴勝不貴久 | Max 1 mission/cycle, focus critical |
| Mỗi ngày tốn ngàn vàng | 日費千金 | Token budget gate |
| Có chỗ không nên tranh | 有所不爭 | DEFER low-impact issues |
