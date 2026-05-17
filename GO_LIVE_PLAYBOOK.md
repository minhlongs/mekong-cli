# Mekong IDE — GO-LIVE PLAYBOOK

> Run this top-to-bottom. The state of the world after each step is verified
> by a command — don't move on if the verification fails. The bottom row of
> [`GO_LIVE_REPORT.md`](./GO_LIVE_REPORT.md) flips to ✅ only after Step 5.

**Pre-conditions** (all already true today):
- `api.cashclaw.cc` returns 200 ✓
- `www.mekongmind.com` is live ✓
- 3 Polar checkout URLs return 302 ✓

**Definition of done:** a non-employee paid $49 → received credits → ran one
paid command. That's XONG.

---

## Step 0 · Sanity check before you touch anything (2 min)

```bash
cd ~/mekong-cli
git status                     # working tree clean? if not, stash or commit
git pull --ff-only              # latest main
grep -rln "<<<<<<<" --exclude-dir=node_modules --exclude-dir=.git \
  --exclude-dir=.venv --exclude-dir=.venv-seed \
  --exclude-dir=plans --exclude-dir=target --exclude-dir=.turbo .
```

The grep must return **nothing** (or only binary build artifacts you can
ignore). If it lists `.tsx` / `.ts` / `.py` / `.json` / `.md`, fix those
conflicts first.

---

## Step 1 · Build the dashboard locally (10 min)

```bash
cd ~/mekong-cli/apps/dashboard
cp .env.local.example .env.local
# fill in NEXT_PUBLIC_SUPABASE_URL + SUPABASE_SERVICE_KEY (free Supabase tier)

npm install                 # first time only
npm run build               # MUST exit 0. ignoreBuildErrors is on, so type
                            # errors are warnings, not blockers.
npm run start               # http://localhost:3000 → /dashboard
```

**Verify:** open http://localhost:3000/dashboard in a browser. You should see
a cream/ink Claude-styled page (NOT the old `bg-slate-950` dark blue — if you
do, the new design tokens didn't load; check `globals.css` imports
`claude-design.css`).

If the build fails with a *non-type* error (missing module, syntax error,
ENOENT), that's real — fix it before continuing.

---

## Step 2 · Deploy to Cloudflare Pages (10 min)

Pre-req: `wrangler login` once (opens browser).

```bash
cd ~/mekong-cli
./scripts/deploy-dashboard.sh
```

The script:
1. Installs deps if missing
2. Runs `npm run build`
3. Deploys `.next` to Cloudflare Pages project `mekong-ide`

**First-time only — set production env vars in Cloudflare UI:**
- Cloudflare Dashboard → Pages → `mekong-ide` → Settings → Environment variables
- Add (Production):
  - `NEXT_PUBLIC_SUPABASE_URL`
  - `SUPABASE_SERVICE_KEY`
  - (optional) `POLAR_PRODUCT_STARTER`, `POLAR_PRODUCT_GROWTH`,
    `POLAR_PRODUCT_PRO`, `POLAR_WEBHOOK_SECRET`

**Map custom domain — first time only:**
- Cloudflare Dashboard → Pages → `mekong-ide` → Custom domains → Add
  `ide.mekongmind.com`. CF auto-creates the CNAME because the domain is on
  Cloudflare DNS already.

**Verify:**
```bash
curl -sI https://ide.mekongmind.com | head -1
# expect: HTTP/2 200
```

If you get 522 / 525 / 1014, the custom domain isn't mapped yet — wait 2–5
minutes after adding it.

---

## Step 3 · Smoke-test the payment loop (5 min)

```bash
./scripts/smoke-test-payment.sh
```

What it checks (no real charge):
1. Gateway health
2. `/v1/pricing` returns 3 checkout URLs
3. Each Polar URL returns 302
4. `/v1/auth/me` rejects unauthenticated requests with 401
5. Webhook HMAC verifier loads
6. Credit deduction logic dry-run

All 6 must be green. If 1–4 fail, the gateway or Polar wiring drifted —
check `STRATEGY.md` against actual config. If 5–6 fail, the issue is in code
(`lib/billing` or `core/credits`).

---

## Step 4 · Founder dry-run — buy the product yourself (15 min)

This is the ONLY way to verify the webhook → credit-deduct path on a real
customer. Use a real card, on a real account that is not in your team.

1. Open https://buy.polar.sh/a09a5fa0-63db-42a4-a547-3b1523ffc263 (Starter
   $49).
2. Pay with a personal card (NOT a company / dev card if those are
   whitelisted to bypass billing). Use your wife's / co-founder's email if
   you want a clean separation from internal accounts.
3. **Within 60 s** check:
   ```bash
   # webhook arrived?
   curl -sH "Authorization: Bearer $ADMIN_TOKEN" \
     https://api.cashclaw.cc/v1/webhooks/recent | jq

   # tenant got 200 credits?
   curl -sH "Authorization: Bearer $YOUR_TOKEN" \
     https://api.cashclaw.cc/v1/me/credits | jq
   ```
4. Run one real paid command:
   ```bash
   mekong cook "Build me a hello-world FastAPI"
   # check credits decreased by N
   curl -sH "Authorization: Bearer $YOUR_TOKEN" \
     https://api.cashclaw.cc/v1/me/credits | jq
   ```

If credits don't deduct, the gateway's `pricing.deduct_credits` isn't being
called on success path. Fix before announcing.

---

## Step 5 · External customer (the real XONG)

When the next non-employee buys:

1. Append a row to `GO_LIVE_REPORT.md` Release history.
2. Flip "First external paying customer" to ✅ with date + Polar order id.
3. Send a thank-you email manually (skip automation until you have 10 of
   these).
4. Tweet/post about it. Now you can update README to remove the "not yet"
   markers.

---

## Step 6 · Update marketing claims (1 day, after Step 5)

- README — change the status table to all ✅ for the rows that actually are.
- Remove "443 commands" → use the actual count from
  `find .claude/commands -name "*.md" | wc -l`.
- Replace "OpenClaw daemon — shipping in v6.1" with the truth: either ship
  it (cut scope to 1 working mission), or change copy to "in alpha — solo
  founders can opt in via `mekong daemon --experimental`".

---

## Common failures & fixes

| Symptom | Cause | Fix |
| --- | --- | --- |
| `npm run build` shows `<<<<<<< HEAD` parse error | another merge conflict snuck in | `grep -rln "<<<<<<<" apps/ --include="*.tsx" --include="*.ts"` and resolve |
| `wrangler pages deploy` says "project not found" | wrangler not logged in or wrong account | `wrangler login`, then re-run |
| `ide.mekongmind.com` returns CF error page | custom domain not mapped or DNS not propagated | Cloudflare Dashboard → Pages → `mekong-ide` → Custom domains |
| Polar webhook doesn't fire | wrong `POLAR_WEBHOOK_SECRET` in CF env, OR webhook URL not registered in Polar dashboard | Polar Dashboard → Webhooks → check URL = `https://api.cashclaw.cc/v1/webhooks/polar` |
| Credits don't deduct after webhook | webhook event type mismatch (e.g. `subscription.created` vs `order.created`) | Add log in `app/api/polar/webhook/route.ts`, replay event from Polar UI |
| Dashboard renders dark blue / Tailwind defaults | `claude-design.css` import order wrong | confirm `globals.css` imports it AFTER the `md-sys-*` files |

---

## Roll-back (if Step 4 fails badly)

```bash
# revert the most recent dashboard deploy
cd ~/mekong-cli
git log --oneline apps/dashboard | head -5
git revert <bad-commit>
./scripts/deploy-dashboard.sh
```

If the gateway itself broke (rare — you didn't deploy it in this playbook),
restart the local M1 Max process: `cd ~/mekong-cli && make api-restart`.

---

## What this playbook deliberately does NOT do

- **No CI/CD setup.** Add it after Step 5 — `.github/workflows/dashboard.yml`
  triggers `scripts/deploy-dashboard.sh` on push to `main`. Today the founder
  deploys manually so blast radius is bounded.
- **No OpenClaw daemon launch.** That's a separate playbook. Today you ship
  a manual product. Daemon is v6.1+.
- **No multi-tenant billing tests.** One tenant (you) is enough for go-live.
  Multi-tenant edge cases come after 10 customers.

The whole thing fits in a 90-minute focused session if pre-conditions hold.
Stop bikeshedding and run it.
