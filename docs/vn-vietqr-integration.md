# VietQR Auto-Conversion — Founder Setup Guide

> Phase 7 P02 — when an OPC pilot pays via VietQR bank transfer, the
> gateway records the conversion automatically. No founder manual step.

## What This Replaces

Phase 6 manual flow:
1. OPC user transfers 199K VND via VietQR to founder's bank account
2. Founder sees transfer in bank app → opens Mekong admin
3. Founder runs `curl POST /v1/pilot/convert -H "Authorization: Bearer ..."`

Phase 7 automated flow:
1. OPC user transfers 199K VND via VietQR with memo `MEKONG-opc_001_xxx`
2. Bank webhook fires → gateway records conversion + MRR updates
3. Founder sees notification (optional, via separate webhook) — no action needed

## Why Sepay (Default)

| Provider | Setup time | Cost | Verifier impl status |
|----------|-----------|------|----------------------|
| **Sepay** | ~10 min | Free tier 100 tx/mo | ✅ shipped |
| MB Bank Open API | 2-3 weeks (KYC) | Enterprise contract | ❌ designed only |
| VietQR.io aggregator | ~30 min | ~500K VND/mo | ❌ designed only |

For 1-person ops scaling 10→100 pilots, Sepay's free tier exactly fits.
Upgrade path documented at end of this guide.

## Founder Setup Steps

### 1. Sign Up for Sepay

1. Visit https://sepay.vn → sign up with founder's bank account email
2. Verify email + add bank account (MB / VCB / TCB / VIB supported)
3. Confirm small test deposit (~5K VND) — typically 5-10 minutes

### 2. Configure Sepay Webhook

In Sepay dashboard → Settings → Webhooks:

- **URL:** `https://gateway.cashclaw.cc/v1/payments/vietqr/webhook`
- **Events:** `transaction.received` (incoming transfers only)
- **Signature method:** HMAC-SHA256
- **Secret:** generate via:
  ```bash
  python3 -c "import secrets; print(secrets.token_urlsafe(32))"
  ```
- Save the secret to a notes file — needed in step 3.

### 3. Inject Secret into Gateway

Edit `/Library/LaunchDaemons/com.mekong.gateway.plist`, add to
`EnvironmentVariables` dict:

```xml
<key>MEKONG_VIETQR_PROVIDER</key>
<string>sepay</string>
<key>MEKONG_VIETQR_WEBHOOK_SECRET</key>
<string>PASTE-YOUR-SEPAY-SECRET-HERE</string>
```

Restart gateway:

```bash
sudo launchctl kickstart -k system/com.mekong.gateway
```

Verify endpoint live:

```bash
curl -s -o /dev/null -w "%{http_code}\n" -X POST \
  -H "Content-Type: application/json" \
  -d '{"tx_ref":"setup_check","amount":1000,"memo":""}' \
  https://gateway.cashclaw.cc/v1/payments/vietqr/webhook
# Expect: 401 (signature missing) — proves feature enabled.
# If 503 → secret not loaded; check plist + kickstart.
```

### 4. Configure QR Memo Format

On the OPC pilot welcome page / payment page, generate VietQR codes with
memo pre-filled in this format:

```
MEKONG-{user_id}
```

Example: user `opc_001_abc12` paying 199K VND tier → memo `MEKONG-opc_001_abc12`.

VietQR.io generator: https://vietqr.io/api → set `addInfo` param to the
memo string. Memo lookup regex is case-insensitive + tolerates extra
whitespace, so user typos generally don't break the flow.

### 5. Test End-to-End

Use Sepay's webhook test feature (or a real 1K VND transfer):

1. Send test payload with memo `MEKONG-opc_001_yourtest` and amount `199000`
2. Tail logs: `tail -f /var/log/mekong-gateway.log` + `tail -f ~/.mekong/vietqr_webhook.log`
3. Confirm `vietqr_webhook.log` shows `"outcome": "converted"` for that tx_ref
4. Verify: `curl -s https://gateway.cashclaw.cc/v1/pilot/revenue | jq .mrr_vnd`
   — must reflect the new 199K addition

## Operational Notes

### Idempotency

Same `bank_tx_ref` returns `{"status": "already_processed"}` — no MRR
double-count. Sepay may retry up to 3 times per their docs; subsequent
deliveries are no-ops on our side.

### Error Policy (Bank-Friendly)

| Outcome | HTTP | Why |
|---------|------|-----|
| Conversion recorded | 200 | Normal success |
| Already processed (duplicate ref) | 200 | Idempotent retry |
| Memo unparseable | 200 | Log + accept; founder reviews log |
| Amount not a known tier | 200 | Log + accept; manual reconcile later |
| Unknown user_id (memo OK but no pilot) | 200 | Log + accept |
| Invalid signature | 401 | Stops bank retry cycle |
| Secret not configured (gateway-side) | 503 | Feature disabled |

The bank should NEVER see 5xx from app logic — only signature failures.

### Log Review (Founder Weekly Task)

```bash
# All webhook attempts last 7 days
tail -n 200 ~/.mekong/vietqr_webhook.log | jq -s 'sort_by(.recorded_at)'

# Filter problematic outcomes
jq -c 'select(.outcome != "converted" and .outcome != "already_processed")' \
  ~/.mekong/vietqr_webhook.log
```

### Secret Rotation

Same procedure as admin token rotation:
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"  # generate
# → paste into Sepay dashboard AND plist
sudo launchctl kickstart -k system/com.mekong.gateway
```

## When to Upgrade From Sepay

- **>80 tx/mo for 2 months running** → approaching 100 free tier limit
- **Need >1 bank account** → Sepay free tier is per-account
- **Need MB Bank-specific features** (e.g., bulk disbursement) →
  implement `MBVerifier` in `src/services/vietqr_verifier.py`

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| All webhooks 401 | Wrong secret | Sync secret between Sepay dashboard + plist |
| All webhooks 503 | `MEKONG_VIETQR_WEBHOOK_SECRET` unset | Edit plist, kickstart |
| Conversions miss user | Memo parsing fail | Check `~/.mekong/vietqr_webhook.log` for `memo_unparseable` outcomes |
| Duplicate MRR records | (Shouldn't happen) | Check `bank_tx_ref` field — file an issue |
| Bank not delivering | Sepay outage / wrong URL | Test with `curl` against the URL Sepay has |

## Related Docs

- `docs/handoff-shipping-playbook.md` — overall ship/handoff chain
- `infra/launchd/README.md` — gateway plist management
- CLAUDE.md § "VietQR webhook" — env var reference
