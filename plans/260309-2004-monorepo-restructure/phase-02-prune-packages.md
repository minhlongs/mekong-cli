# Phase 2: Cắt Tỉa packages/ — Xóa Stubs, Gộp Trùng Lặp

## Overview
- **Ưu tiên:** P0 CRITICAL
- **Trạng thái:** TODO
- **Mô tả:** 115 packages, ~52 là stub (≤5 files). Cắt xuống còn ~15-20 packages thực sự có giá trị.

## Phân Tích Hiện Tại

### Nhóm 1: PACKAGES CÓ GIÁ TRỊ (GIỮ) — ~15 packages

| Package | Files | Mô tả |
|---------|-------|-------|
| `cleo/` | 255 | Submodule — task management CLI |
| `agents/` | 101 | Agent framework |
| `core/` | 36 | Shared types, utils |
| `trading-core/` | 23 | Exchange connectors |
| `vibe-arbitrage-engine/` | 28 | Trading engine |
| `vibe-payment/` | 25 | Payment SDK |
| `vibe-ui/` | 23 | React components |
| `vibe-auth/` | 21 | Auth utilities |
| `business/` | 21 | Business logic |
| `tooling/` | 19 | Build tools |
| `memory/` | 17 | Memory store |
| `mekong-engine/` | 17 | Core engine |
| `vibe-analytics/` | 16 | Analytics |
| `vibe-money/` | 16 | Financial utils |
| `ui/` | 16 | UI components (trùng với vibe-ui?) |
| `observability/` | 13 | Logging/metrics |
| `ai-hub-sdk/` | 13 | AI integrations |
| `shared/` | ? | Shared utilities |
| `billing/` | ? | Billing logic |
| `i18n/` | ? | Internationalization |
| `integrations/` | ? | External integrations |
| `openclaw-agents/` | ? | OpenClaw agents |

### Nhóm 2: HUB-SDK STUBS (XÓA) — ~30 packages

Đây là các industry-specific SDKs được scaffold nhưng chưa implement:

```
agritech-hub-sdk, automotive-hub-sdk, commerce-hub-sdk,
construction-hub-sdk, creator-marketing-hub-sdk, devtools-hub-sdk,
education-hub-sdk, energy-hub-sdk, events-hub-sdk, fashion-hub-sdk,
fintech-hub-sdk, fnb-hub-sdk, gaming-hub-sdk, govtech-hub-sdk,
healthcare-hub-sdk, hospitality-hub-sdk, identity-compliance-sdk,
industry-hub-sdk, infra-hub-sdk, insurtech-hub-sdk, legal-hub-sdk,
logistics-hub-sdk, manufacturing-hub-sdk, media-hub-sdk,
multi-org-billing-sdk, nonprofit-hub-sdk, ops-hub-sdk,
people-hub-sdk, pharma-hub-sdk, proptech-hub-sdk, saas-hub-sdk,
sustainability-hub-sdk, telecom-hub-sdk, travel-hub-sdk,
web3-hub-sdk, webhook-billing-sdk, wellness-hub-sdk
```

### Nhóm 3: VIBE-* STUBS (XÓA hoặc GỘP) — ~30 packages

```
vibe-agent, vibe-agents (trùng?), vibe-ai-safety, vibe-billing,
vibe-billing-hooks, vibe-billing-trading, vibe-bridge, vibe-climate,
vibe-compliance, vibe-compliance-auto, vibe-composable-commerce,
vibe-consent, vibe-construction, vibe-creator-economy, vibe-crm,
vibe-customer-success, vibe-dev, vibe-digital-therapeutics,
vibe-digital-twin, vibe-ecommerce, vibe-edge, vibe-embedded-finance,
vibe-fnb, vibe-food-tech, vibe-hr, vibe-identity, vibe-logistics,
vibe-longevity, vibe-marketing, vibe-media-trust, vibe-money,
vibe-newsletter, vibe-notifications, vibe-observability, vibe-ops,
vibe-payment-router, vibe-payos-billing-types, vibe-physical-ai,
vibe-pos, vibe-revenue, vibe-robotics, vibe-space-tech, vibe-spatial,
vibe-stripe, vibe-subscription, vibe-subscription-webhooks,
vibe-supabase, vibe-video-intel, vibe-wellbeing, vibe-wellness
```

### Nhóm 4: TRÙNG LẶP CẦN GỘP

| Cặp trùng | Hành động |
|------------|----------|
| `ui/` + `vibe-ui/` | Gộp → `packages/ui/` |
| `vibe-agent/` + `vibe-agents/` + `agents/` | Gộp → `packages/agents/` |
| `vibe-billing/` + `billing/` + `vibe-billing-hooks/` + `vibe-billing-trading/` | Gộp → `packages/billing/` |
| `vibe-observability/` + `observability/` | Gộp → `packages/observability/` |
| `vibe-newsletter/` + `newsletter/` | Gộp → `packages/newsletter/` |
| `docs/` (packages) + `docs/` (apps) + `docs/` (root) | Clarify mỗi cái là gì |
| `mekong-engine/` + `mekong-clawwork/` + `mekong-moltbook/` | Đánh giá gộp |

## Implementation Steps

### Bước 1: Kiểm tra imports trước khi xóa
```bash
# Tìm xem có app nào import từ hub-sdk packages không
for pkg in agritech-hub-sdk automotive-hub-sdk commerce-hub-sdk; do
  echo "=== $pkg ==="
  grep -r "$pkg" apps/ packages/ src/ --include="*.js" --include="*.ts" --include="*.json" -l
done
```

### Bước 2: Xóa hub-sdk stubs (1 commit)
```bash
# Sau khi verify không có import
git rm -r packages/*-hub-sdk
```

### Bước 3: Xóa vibe-* stubs (1 commit)
```bash
# Giữ lại: vibe-arbitrage-engine, vibe-payment, vibe-ui, vibe-auth, vibe-analytics, vibe-money
# Xóa phần còn lại sau khi verify
```

### Bước 4: Gộp packages trùng lặp
- `vibe-ui/` code → `ui/`
- `vibe-agents/` code → `agents/`
- `vibe-billing*/` code → `billing/`

### Bước 5: Cập nhật pnpm-workspace.yaml
```yaml
packages:
  - 'packages/*'
  - 'apps/*'
```

## Kiến Trúc Packages Sau Cắt Tỉa (~15-20)

```
packages/
├── agents/              # Agent framework (gộp vibe-agent, vibe-agents)
├── auth/                # Auth utilities (rename vibe-auth)
├── billing/             # Billing logic (gộp vibe-billing*)
├── build-optimizer/     # Build tools
├── business/            # Business logic
├── cleo/                # Task management (submodule)
├── core/                # Shared types, constants
├── i18n/                # Internationalization
├── integrations/        # External integrations
├── mekong-engine/       # Core execution engine
├── memory/              # Memory store
├── observability/       # Logging, metrics (gộp vibe-observability)
├── openclaw-agents/     # OpenClaw-specific agents
├── shared/              # Shared utilities
├── trading-core/        # Exchange connectors
├── ui/                  # React components (gộp vibe-ui)
└── vibe-payment/        # Payment SDK
```

## Todo List

- [ ] Audit imports cho tất cả hub-sdk packages
- [ ] Audit imports cho tất cả vibe-* stub packages
- [ ] Xóa ~30 hub-sdk stubs
- [ ] Xóa ~30 vibe-* stubs
- [ ] Gộp packages trùng lặp (ui, agents, billing, observability)
- [ ] Cập nhật pnpm-workspace.yaml
- [ ] Cập nhật imports trong apps/ nếu cần
- [ ] `pnpm install` verify
- [ ] Tests pass

## Success Criteria

- packages/ giảm từ 115 → ~15-20
- Không còn stub packages (≤5 files, no real code)
- Không còn packages trùng lặp
- Tất cả apps build thành công
- Tests pass

## Rủi Ro

- Một số apps có thể import từ stub packages → kiểm tra trước
- pnpm-lock.yaml sẽ thay đổi lớn → verify install
- Submodule `cleo/` cần giữ nguyên
