# Sophia Project — Login Credentials & API Keys

**Date:** 2026-03-20
**Source:** `apps/sophia-proposal/.env*`

---

## 🔑 Current Credentials (Development)

### Supabase
| Key | Value |
|-----|-------|
| `NEXT_PUBLIC_SUPABASE_URL` | `https://placeholder.supabase.co` |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | `eyJhbGcplaceholder` |
| `SUPABASE_SERVICE_ROLE_KEY` | `eyJhbGcplaceholder` |

### Polar.sh
| Key | Value |
|-----|-------|
| `POLAR_API_KEY` | `sk_test_placeholder` |
| `POLAR_WEBHOOK_SECRET` | `whsec_placeholder` |

### Anthropic
| Key | Value |
|-----|-------|
| `ANTHROPIC_AUTH_TOKEN` | _(empty)_ |

---

## ⚠️ Status: PLACEHOLDER VALUES

Tất cả credentials trong Sophia project đều là **placeholder** — không dùng production được.

### Required Actions:

1. **Supabase:**
   - Create new project at https://supabase.com
   - Replace `NEXT_PUBLIC_SUPABASE_URL` với project URL thật
   - Replace keys với values từ Dashboard → Settings → API

2. **Polar.sh:**
   - Create products at https://polar.sh/dashboard
   - Replace `POLAR_API_KEY` với `sk_live_...` hoặc `sk_test_...`
   - Replace `POLAR_WEBHOOK_SECRET` với `whsec_...`

3. **Anthropic:**
   - Get API key from https://console.anthropic.com
   - Set `ANTHROPIC_AUTH_TOKEN=sk-ant-...`

---

## 📋 Template (.env.example)

```bash
ANTHROPIC_API_KEY=sk-ant-your-api-key-here
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
POLAR_API_URL=https://api.polar.sh
POLAR_API_KEY=sk_live_your_api_key
POLAR_WEBHOOK_SECRET=whsec_your_webhook_secret
```

---

## 🎯 Next Steps

Để lấy credentials thật:

1. **Supabase:**
   ```bash
   # Mở dashboard
   open https://supabase.com/dashboard
   # → Chọn project → Settings → API
   ```

2. **Polar.sh:**
   ```bash
   # Mở dashboard
   open https://polar.sh/dashboard
   # → Settings → API Keys
   ```

3. **Anthropic:**
   ```bash
   # Mở dashboard
   open https://console.anthropic.com/settings/keys
   ```

---

**Report:** `/plans/reports/sophia-credentials-260320-0132.md`
