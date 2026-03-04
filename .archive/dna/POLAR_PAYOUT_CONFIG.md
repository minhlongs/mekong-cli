# 🏦 POLAR.SH PAYOUT CONFIGURATION - GLOBAL

> **Dùng cho tất cả projects trong mekong-cli ecosystem**
> Last updated: 2026-02-06

---

## ✅ Bank Account Details (Vietnam)

| Field               | Value                                                         |
| ------------------- | ------------------------------------------------------------- |
| **Bank**            | ACB (Asia Commercial Joint Stock Bank)                        |
| **Account Number**  | `5566776868`                                                  |
| **Account Holder**  | `TRẦN THIỆN LÂM`                                              |
| **Branch**          | ACB Chi nhánh Đồng Tháp                                       |
| **CITID/Bank Code** | `87307001`                                                    |
| **Address**         | 352 Nguyen Sinh Sac, Sa Dec Ward, Dong Thap Province, Vietnam |

---

## 🔧 Polar.sh Integration Config

### Environment Variables (Copy to .env.local)

```bash
# Polar.sh Configuration
POLAR_ACCESS_TOKEN=polar_oat_xxx      # Get from Polar Dashboard > Settings > Developer
POLAR_WEBHOOK_SECRET=whsec_xxx        # Get from Polar Webhooks settings
POLAR_ORGANIZATION_ID=org_xxx         # Your org ID from Dashboard
NEXT_PUBLIC_POLAR_SANDBOX=false       # Set true for testing

# Product IDs (Create in Polar Dashboard)
POLAR_PRODUCT_ID_STARTER=prod_xxx     # Tier 1: $1,200
POLAR_PRODUCT_ID_GROWTH=prod_xxx      # Tier 2: $2,000
POLAR_PRODUCT_ID_PREMIUM=prod_xxx     # Tier 3: $3,000
```

### SDK Packages

```bash
npm install @polar-sh/sdk @polar-sh/nextjs
```

### API Endpoints

| Environment | URL                               |
| ----------- | --------------------------------- |
| Production  | `https://api.polar.sh/v1`         |
| Sandbox     | `https://sandbox-api.polar.sh/v1` |

---

## 💰 Payout Info

| Feature             | Details                             |
| ------------------- | ----------------------------------- |
| **Payout Method**   | Polar → Wise → ACB (Direct VN Bank) |
| **Fee**             | 4% + $0.40 per transaction          |
| **Withdrawal**      | Anytime (không phải đợi cuối tháng) |
| **Processing Time** | 1-4 ngày làm việc                   |

---

## 📋 Projects Using Polar

- [x] Sophia AI Factory - `apps/sophia-ai-factory`
- [ ] AgencyOS RaaS Credits - `apps/engine` (pending)
- [ ] 84tea Premium Features - `apps/84tea` (future)

---

## 🔗 References

- Polar Dashboard: https://polar.sh/dashboard
- Polar Docs: https://docs.polar.sh
- Acceptable Use: https://docs.polar.sh/merchant-of-record/acceptable-use
- vnROM Article: https://vnrom.net/2025/04/danh-gia-polar-sh-merchant-of-record-tot-nhat-cho-developer-viet/

---

---

## 🤖 Auto Balance Checker

Polar **không có auto payout** - phải rút thủ công. Script sau sẽ check balance và notify:

### Files

- `scripts/polar-balance-checker.ts` - Check balance & Telegram notify
- `scripts/setup-polar-cron.sh` - Setup cron job (mỗi 6 giờ)

### Setup Cron

```bash
# Make executable
chmod +x scripts/setup-polar-cron.sh

# Run setup
./scripts/setup-polar-cron.sh

# Or manual test
npx ts-node scripts/polar-balance-checker.ts
```

### Environment Variables

```bash
# Required
POLAR_ACCESS_TOKEN=polar_oat_xxx

# Optional (for Telegram alerts)
TELEGRAM_BOT_TOKEN=123456:ABC...
TELEGRAM_CHAT_ID=your_chat_id
```

---

_Genesis: 2026-02-06 | Global Payment Config_
