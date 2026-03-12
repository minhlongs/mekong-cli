# HƯỚNG DẪN SỬ DỤNG v0.2.0 — Feed cho Opus CC CLI

## Kiểm tra trước khi bắt đầu

```bash
cd mekong-cli
git status          # phải clean
pnpm build          # phải pass
pnpm test           # phải pass
mekong --help       # phải chạy
git log --oneline   # verify v0.1.0 commits có đủ
```

Nếu bất kỳ check nào fail → fix v0.1.0 trước. KHÔNG bắt đầu v0.2.0 trên nền bị lỗi.

---

## Chuẩn bị

```bash
# Update CLAUDE.md
cp path/to/CLAUDE.md ./CLAUDE.md    # overwrite v0.1.0 CLAUDE.md

# Install new deps
pnpm add nodemailer googleapis stripe handlebars date-fns cron markdown-table csv-parse csv-stringify
pnpm add -D @types/nodemailer @types/cron

# Commit
git add -A && git commit -m "chore: upgrade deps for v0.2.0"

# Create branch
git checkout -b v0.2.0
```

---

## Quy trình: 5 Sessions

### SESSION 1 — Types + Stores (15 phút)

Kéo `IMPLEMENTATION-SPEC-v0.2.md` vào, rồi gõ:

```
Đọc CLAUDE.md và IMPLEMENTATION-SPEC-v0.2.md.

Đây là upgrade từ v0.1.0. KHÔNG sửa code v0.1.0. Chỉ THÊM files mới.

Làm theo thứ tự:
1. Tạo folder structure mới (Section 2) — chỉ tạo folders/files mới
2. Code src/integrations/types.ts (Section 3.1)
3. Code src/crm/types.ts (Section 3.2)
4. Code src/finance/types.ts (Section 3.3)
5. Code src/dashboard/types.ts (Section 3.4)
6. Code src/crm/store.ts (Section 5.1)
7. Code src/finance/store.ts (Section 6.1)
8. Viết tests cho CrmStore (CRUD operations cho leads, customers, tickets)
9. Viết tests cho FinanceStore (CRUD operations cho invoices, expenses, revenue)
10. Chạy pnpm lint && pnpm test

STOP sau bước 10.
```

**Review → commit:**
```bash
git add -A && git commit -m "feat(v0.2): types + data stores for CRM and finance"
```

---

### SESSION 2 — Integrations (20 phút)

Mở session mới:

```
Đọc CLAUDE.md và IMPLEMENTATION-SPEC-v0.2.md.

Tiếp tục v0.2.0 upgrade. Code integrations layer:

1. Code src/integrations/index.ts — IntegrationRegistry (Section 4.1)
   - Register, connect, disconnect, healthCheck, list
   - Credentials saved to ~/.mekong/credentials.json

2. Code src/integrations/stripe/client.ts (Section 4.2)
   - Tất cả methods return mock data nếu chưa connect (graceful degradation)
   - createInvoice, sendInvoice, getPaymentStatus, listRecentPayments, getBalance

3. Code src/integrations/stripe/types.ts — types riêng cho Stripe mapping

4. Code src/integrations/email/sender.ts (Section 4.3)
   - Rate limit 20/hour là HARD LIMIT
   - send() phải check rate limit trước khi gửi

5. Code src/integrations/email/templates.ts (Section 4.4)
   - 7 built-in templates
   - render() trả về {subject, body}

6. Code src/integrations/calendar/google.ts (Section 4.5)
   - Stub OAuth flow, mock data cho listEvents/createEvent nếu chưa auth

7. Code src/integrations/notifications/slack.ts
   - Webhook POST đơn giản

8. Code src/integrations/notifications/telegram.ts
   - Bot API sendMessage

9. Code src/integrations/notifications/dispatcher.ts (Section 4.6)
   - Priority routing: critical→all, high→primary+email, normal→primary, low→queue

10. Viết tests cho IntegrationRegistry + EmailSender + NotificationDispatcher
11. Chạy pnpm lint && pnpm test

STOP sau bước 11.
```

**Review → commit:**
```bash
git add -A && git commit -m "feat(v0.2): integrations — stripe, email, calendar, notifications"
```

---

### SESSION 3 — CRM + Finance Business Logic (25 phút)

Mở session mới:

```
Đọc CLAUDE.md và IMPLEMENTATION-SPEC-v0.2.md.

Tiếp tục v0.2.0. Code business logic layer:

1. Code src/crm/leads.ts (Section 5.2)
   - create, qualify (AI), advanceStage, convert, generateFollowUp, getDueFollowUps, getPipeline
   
2. Code src/crm/customers.ts
   - CRUD operations
   - convertFromLead (nhận Lead, tạo Customer)
   - calculateHealthScore (dựa trên: có ticket open không, payment on time không, last activity)
   
3. Code src/crm/support.ts (Section 5.3)
   - create (with auto-triage), triage (AI), draftReply (AI), addMessage, resolve
   - getSlaAtRisk, getSummary
   
4. Code src/crm/pipeline.ts
   - getPipelineView: group leads by status, calc totalValue per stage, calc conversion rates

5. Code src/finance/invoicing.ts (Section 6.2)
   - create, send (Stripe or Email fallback), syncPaymentStatus, sendOverdueReminders
   
6. Code src/finance/expenses.ts
   - add, list, getByCategory, getRecurring, getMonthlySummary

7. Code src/finance/revenue.ts (Section 6.3)
   - record, calculateMrr, generateSummary, calculateRunway
   
8. Code src/finance/reports.ts (Section 6.4)
   - monthlyClose, renderCliTable, renderMarkdown, exportCsv

9. Viết tests cho:
   - LeadManager.create + qualify
   - SupportManager.create + triage
   - InvoiceManager.create
   - RevenueTracker.calculateMrr

10. Chạy pnpm lint && pnpm test

STOP sau bước 10.
```

**Review → commit:**
```bash
git add -A && git commit -m "feat(v0.2): CRM leads/support + finance invoicing/revenue"
```

---

### SESSION 4 — Dashboard + Agent Defs + SOP Templates (20 phút)

Mở session mới:

```
Đọc CLAUDE.md và IMPLEMENTATION-SPEC-v0.2.md.

Tiếp tục v0.2.0. Code dashboard + templates:

1. Code src/dashboard/metrics-aggregator.ts
   - Collect data from CRM, Finance, SOP metrics, Budget tracker
   - Return unified metrics object

2. Code src/dashboard/daily-standup.ts (Section 7.1)
   - generate(): query yesterday activity + today scheduled
   - renderCli(): chalk-colored output

3. Code src/dashboard/weekly-digest.ts (Section 7.2)
   - generate(): full week summary + AI insights
   - renderMarkdown() + renderCli()

4. Code src/dashboard/renderer.ts (Section 7.3)
   - buildBoard(): aggregate all module data → AndonBoard
   - render(): beautiful CLI output with chalk

5. Tạo 4 agent definition files (Section 8):
   - src/agents/definitions/finance-agent.yaml
   - src/agents/definitions/sales-agent.yaml
   - src/agents/definitions/support-agent.yaml
   - src/agents/definitions/scheduler-agent.yaml

6. Tạo 10 SOP template files (Section 9):
   - src/sops/templates/invoice-send.yaml
   - src/sops/templates/expense-log.yaml
   - src/sops/templates/monthly-close.yaml
   - src/sops/templates/lead-qualify.yaml
   - src/sops/templates/customer-onboard.yaml
   - src/sops/templates/support-triage.yaml
   - src/sops/templates/weekly-report.yaml
   - src/sops/templates/daily-standup.yaml
   - src/sops/templates/email-campaign.yaml
   - src/sops/templates/payment-followup.yaml

7. Viết test cho DailyStandupGenerator.generate()
8. Viết test cho DashboardRenderer.render()
9. Chạy pnpm lint && pnpm test

STOP sau bước 9.
```

**Review → commit:**
```bash
git add -A && git commit -m "feat(v0.2): dashboard + 4 agents + 10 SOP templates"
```

---

### SESSION 5 — CLI Commands + Config + Wiring (20 phút)

Mở session mới:

```
Đọc CLAUDE.md và IMPLEMENTATION-SPEC-v0.2.md.

Tiếp tục v0.2.0. Final session — wire everything together:

1. Update src/config/schema.ts:
   - EXTEND ConfigSchema (dùng .extend() hoặc .merge()), ĐỪNG replace
   - Thêm: integrations, crm, finance, dashboard sections (Section 10)

2. Code src/cli/commands/crm.ts (Section 11.1)
   - Tất cả subcommands: lead add/list/qualify/followup, customer list/onboard, ticket create/list/triage, pipeline, summary

3. Code src/cli/commands/finance.ts (Section 11.2)
   - Tất cả subcommands: invoice create/send/list, expense add/list, revenue, report, runway, export

4. Code src/cli/commands/dashboard.ts (Section 11.3)
   - dashboard (Andon board), dashboard standup, dashboard weekly, dashboard --watch

5. Update src/cli/index.ts — register 3 new commands (Section 11.4)

6. Update src/core/scheduler.ts:
   - Thêm scheduled_sops support
   - Parse cron expressions
   - Auto-run SOPs on schedule

7. Update src/core/engine.ts:
   - Register IntegrationRegistry
   - Register CRM modules
   - Register Finance modules
   - Register Dashboard modules
   - Initialize integrations on startup

8. Update default mekong.yaml template (Section 10)

9. Chạy pnpm build
10. Test CLI commands:
    - mekong dashboard
    - mekong crm summary
    - mekong finance revenue
    - mekong crm lead list
    - mekong finance invoice list
    - mekong sop list (phải show 15 templates: 5 v0.1 + 10 v0.2)

11. Update README.md — thêm v0.2.0 features
12. Chạy pnpm lint && pnpm test

STOP sau bước 12.
```

**Review → commit & tag:**
```bash
git add -A && git commit -m "feat(v0.2): CLI commands + config + wiring — v0.2.0 complete"
git tag v0.2.0
git checkout main
git merge v0.2.0
```

---

## Quy tắc Jidoka cho v0.2.0

Tất cả rules từ v0.1.0 VẪN ÁP DỤNG, thêm:

- Nếu Opus **sửa file v0.1.0** mà spec không yêu cầu → REJECT ngay
- Nếu Opus **replace ConfigSchema** thay vì extend → yêu cầu dùng .extend()
- Nếu Opus **import trực tiếp Stripe SDK trong business logic** → yêu cầu đi qua IntegrationRegistry
- Nếu Opus **skip rate limit trong EmailSender** → yêu cầu implement lại
- Nếu Opus **hardcode API keys** → REJECT, phải đọc từ env vars qua config
- Nếu test v0.1.0 bị fail sau khi code v0.2.0 → FIX NGAY, đây là regression

## Sau v0.2.0

Verify full workflow:
```bash
# 1. Init fresh project
mkdir test-company && cd test-company
mekong init

# 2. Check dashboard
mekong dashboard

# 3. Add a lead
mekong crm lead add "John Doe" "john@example.com"

# 4. List SOPs
mekong sop list
# Phải thấy 15 templates

# 5. Run daily standup
mekong sop run daily-standup

# 6. Check finance
mekong finance revenue
```

Nếu tất cả chạy → v0.2.0 done. Ready for v0.3.0 (Kaizen analytics, marketplace, advanced heartbeat).
