# RaaS Dashboard UI Audit Report

**Date:** 2026-03-19
**Project:** `packages/raas-dashboard/`
**Framework:** Astro 5.0 (SSG)
**Language:** TypeScript
**Default Locale:** Vietnamese (vi)

---

## 1. Current Page Tree

```
packages/raas-dashboard/
├── src/
│   ├── layouts/
│   │   └── dashboard-layout.astro       # Master layout (sidebar + topbar)
│   ├── pages/
│   │   ├── index.astro                  # Root redirect (/)
│   │   ├── signup.astro                 # Auth: signup/login
│   │   ├── dashboard.astro              # Dashboard home
│   │   ├── messages.astro               # Thread-based messaging
│   │   ├── content.astro                # Content generation & approval
│   │   ├── contacts.astro               # CRM contacts table
│   │   ├── reports.astro                # Weekly reports
│   │   ├── governance.astro             # Compliance dashboard
│   │   ├── settings.astro               # Business settings
│   │   ├── upgrade.astro                # Pricing tiers
│   │   ├── onboard.astro                # 5-step onboarding wizard
│   │   └── onboarding.astro             # Duplicate of onboard.astro
│   ├── scripts/
│   │   ├── api-client.ts                # API utilities
│   │   └── api-client.js                # Compiled version
│   ├── styles/
│   │   └── dashboard.css                # Global styles
│   ├── i18n/
│   │   ├── vi.json                      # Vietnamese translations
│   │   └── en.json                      # English translations
│   └── public/
│       └── scripts/
│           └── onboard-wizard.js        # Onboarding step logic
├── dist/                                # Build output
├── astro.config.mjs                     # Astro config
├── package.json
└── tsconfig.json
```

---

## 2. Page Analysis

### 2.1 Dashboard Home (`/dashboard`)

**Purpose:** Overview metrics and AI status

**Components:**
- 4 stat cards (messages, contacts, pending content, credits)
- AI status badge
- Recent activity list

**API Endpoints:**
- `GET /v1/reports/overview`
- `GET /billing/credits`

**Gaps:**
- No chart/visualization for trends
- Recent activity is hardcoded text, not actionable

---

### 2.2 Messages (`/messages`)

**Purpose:** Thread-based customer messaging

**Components:**
- Thread list (left pane)
- Message view (right pane)
- Search filter
- Reply input

**API Endpoints:**
- `GET /v1/messages` (list threads)
- `GET /v1/messages/:threadId` (messages)
- `POST /v1/messages/:threadId/reply`

**Gaps:**
- No message templates
- No bulk actions
- No message analytics

---

### 2.3 Content (`/content`)

**Purpose:** AI content generation and approval

**Components:**
- Generate button (7-day content)
- Content list with status badges
- Approve/Reject actions per post

**API Endpoints:**
- `GET /v1/content/posts`
- `POST /v1/content/generate`
- `POST /v1/content/posts/:id/approve`
- `POST /v1/content/posts/:id/reject`

**Gaps:**
- No content calendar view
- No platform filtering
- No content preview before publishing

---

### 2.4 Contacts (`/contacts`)

**Purpose:** CRM contact management

**Components:**
- Search input
- Contact table (name, platform, visits, last contact, status)
- Platform icons (Zalo, Facebook, Instagram)

**API Endpoints:**
- `GET /v1/crm/contacts`

**Gaps:**
- No contact detail view
- No export functionality
- No segment/tag management
- No contact merge

---

### 2.5 Reports (`/reports`)

**Purpose:** Weekly performance reports

**Components:**
- AI summary card
- 4 stat cards (messages, new contacts, posts, response rate)
- Daily breakdown list

**API Endpoints:**
- `GET /v1/reports/weekly`

**Gaps:**
- No date range picker
- No chart visualizations
- No comparison (week-over-week)
- No export to PDF/CSV

---

### 2.6 Governance (`/governance`)

**Purpose:** Compliance and security dashboard

**Components:**
- 4 metric cards (compliance score, audit events, security status, issues)
- 6 governance action cards (privacy policy, terms, GDPR, audit logs, security, data export)
- Compliance trend chart (mock data)
- Security metrics progress bars
- Audit activity list
- Status grid (data security, GDPR, audit trail, backup)

**API Endpoints:** None currently connected (all mock data)

**Gaps:**
- **CRITICAL:** All data is hardcoded mock data
- No real API integration
- Charts are CSS-only, not interactive
- No actual audit log viewer

---

### 2.7 Settings (`/settings`)

**Purpose:** Business and account settings

**Components:**
- Business info display
- API key management (show/copy)
- Current tier display
- Delete account button

**API Endpoints:**
- `GET /v1/business`
- `GET /billing/credits`
- `DELETE /billing/tenants/me`

**Gaps:**
- Cannot edit business info (view-only)
- No API key regeneration
- No team/member management
- No notification preferences

---

### 2.8 Upgrade (`/upgrade`)

**Purpose:** Pricing and tier selection

**Components:**
- 4 tier cards (Starter, Pro, Growth, Enterprise)
- VND payment buttons (via API)
- Polar.sh USD links

**Tiers:**
| Tier | VND | USD | Credits |
|------|-----|-----|---------|
| Starter | 490.000đ | $49 | 200 |
| Pro | 990.000đ | $99 | 500 |
| Growth | 1.490.000đ | $149 | 1000 |
| Enterprise | Contact | $499 | Unlimited |

**API Endpoints:**
- `POST /billing/payment-url`

**Gaps:**
- No current tier highlighting
- No usage history to recommend tier
- No trial option

---

### 2.9 Onboarding (`/onboard`)

**Purpose:** 5-step business setup wizard

**Steps:**
1. Industry selection (Cafe, Restaurant, Spa, Salon, Gym, Other)
2. Business info (name, address, phone, hours)
3. Channel connection (Zalo OA or Facebook Page)
4. Menu/services input
5. AI activation confirmation

**API Endpoints:**
- `POST /v1/onboard/business`
- `POST /v1/onboard/channel`
- `POST /v1/onboard/menu`
- `POST /v1/onboard/activate`

**Gaps:**
- No progress persistence (refresh = restart)
- No skip option for steps
- No menu import (CSV/image upload)

---

### 2.10 Signup (`/signup`)

**Purpose:** Authentication

**Components:**
- Email signup form
- API key login form

**API Endpoints:**
- `POST /billing/tenants` (create tenant)

**Gaps:**
- No email verification flow
- No password (API key only)
- No OAuth options

---

## 3. Component Hierarchy

```
DashboardLayout (dashboard-layout.astro)
├── Sidebar
│   ├── Logo
│   └── Nav (8 items)
├── Topbar
│   ├── Menu Toggle (mobile)
│   ├── Business Name
│   └── Logout Button
└── Main Content (slot)

Shared UI Components (inline in pages):
├── Card (.card)
├── Stat Card (.stat-card)
├── Badge (.badge, .badge-green, .badge-yellow, .badge-gray)
├── Button (.btn, .btn-primary, .btn-secondary, .btn-sm)
├── Input (input, select, textarea)
├── Table (table, th, td)
└── Status Dot (.status-dot)

Page-Specific Components:
├── ThreadItem (messages.astro)
├── ContentPost (content.astro)
├── ContactRow (contacts.astro)
├── MetricCard (governance.astro)
├── GovernanceCard (governance.astro)
├── ChartBar (governance.astro)
├── TierCard (upgrade.astro)
└── StepPanel (onboard.astro)
```

---

## 4. 5-Layer Command Hierarchy Gaps

The 5-layer hierarchy (Founder → Business → Product → Engineering → Ops) requires:

### Layer 1: Founder (Strategy)

**Missing Pages:**
- `/founder/okr` — OKR tracking
- `/founder/swot` — SWOT analysis
- `/founder/kpis` — Executive KPI dashboard
- `/founder/investors` — Investor relations

**Missing Commands:**
- No `/founder` route group
- No strategic planning tools

### Layer 2: Business (Revenue & Operations)

**Missing Pages:**
- `/sales/pipeline` — Sales funnel
- `/marketing/campaigns` — Campaign management
- `/finance/revenue` — Revenue analytics
- `/hr/team` — Team management

**Current Coverage:**
- `/contacts` — Basic CRM (partial)
- `/upgrade` — Pricing (partial)

### Layer 3: Product (Product Management)

**Missing Pages:**
- `/product/roadmap` — Product roadmap
- `/product/feedback` — Customer feedback
- `/product/analytics` — Product analytics

**Current Coverage:**
- `/content` — Content management (partial)

### Layer 4: Engineering (Build & Ship)

**Missing Pages:**
- `/engineering/deployments` — Deployment status
- `/engineering/api` — API docs
- `/engineering/incidents` — Incident management

**Current Coverage:**
- None (dashboard is business-focused)

### Layer 5: Ops (Monitor & Maintain)

**Missing Pages:**
- `/ops/health` — System health
- `/ops/security` — Security monitoring
- `/ops/audit` — Audit logs

**Current Coverage:**
- `/governance` — Compliance (mock data only)
- `/reports` — Weekly reports (partial)

---

## 5. Responsive Design Status

### Current Implementation

**Breakpoints:**
- Mobile: `<= 768px`
- Tablet: `<= 1024px`
- Desktop: `> 1024px`

**Responsive Features:**
- Sidebar collapses to off-canvas menu on mobile
- Menu toggle button with overlay
- Grid layouts use `auto-fit` and `minmax()`
- Touch-friendly button sizes

**Coverage by Page:**

| Page | Mobile | Tablet | Issues |
|------|--------|--------|--------|
| `/dashboard` | ✅ | ✅ | Stat cards stack well |
| `/messages` | ⚠️ | ✅ | Thread list too narrow on small screens |
| `/content` | ✅ | ✅ | Grid adapts properly |
| `/contacts` | ⚠️ | ✅ | Table overflows (has `overflow-x:auto`) |
| `/reports` | ✅ | ✅ | Grid adapts properly |
| `/governance` | ⚠️ | ⚠️ | Complex charts break at 768px |
| `/settings` | ✅ | ✅ | Single column layout |
| `/upgrade` | ✅ | ✅ | Tier grid stacks |
| `/onboard` | ✅ | ✅ | Single column flow |
| `/signup` | ✅ | ✅ | Centered card |

### Issues Found

1. **Messages page:** Thread list at `280px` fixed width—too narrow on mobile
2. **Contacts table:** Horizontal scroll required on mobile (acceptable)
3. **Governance charts:** CSS bar charts don't adapt well to small screens
4. **Topbar business name:** Can overflow on very small screens
5. **No print styles:** Reports page not print-friendly

---

## 6. API Integration Status

| Page | API Connected | Data Source |
|------|---------------|-------------|
| `/dashboard` | ✅ | Live |
| `/messages` | ✅ | Live |
| `/content` | ✅ | Live |
| `/contacts` | ✅ | Live |
| `/reports` | ✅ | Live |
| `/governance` | ❌ | Mock data (hardcoded) |
| `/settings` | ✅ | Live |
| `/upgrade` | ✅ | Live |
| `/onboard` | ✅ | Live |
| `/signup` | ✅ | Live |

---

## 7. Recommendations

### Immediate Fixes

1. **Governance page:** Connect to real API endpoints
2. **Messages page:** Make thread list responsive (flexible width)
3. **Contacts table:** Add export to CSV
4. **Onboarding:** Add localStorage persistence per step

### 5-Layer Expansion Priority

| Priority | Layer | Pages to Add |
|----------|-------|--------------|
| P0 | Ops | `/ops/health`, `/ops/security` |
| P1 | Business | `/sales/pipeline`, `/finance/revenue` |
| P2 | Founder | `/founder/kpis`, `/founder/okr` |
| P3 | Product | `/product/roadmap`, `/product/feedback` |
| P4 | Engineering | `/engineering/status` |

### Component Extraction

Recommended shared components (move to `packages/ui/`):

```
packages/ui/
├── Card.astro
├── StatCard.astro
├── Badge.astro
├── Button.astro
├── Input.astro
├── Table.astro
├── Sidebar.astro
├── Topbar.astro
├── MetricCard.astro
├── ChartCard.astro
└── TierCard.astro
```

---

## 8. Unresolved Questions

1. Should governance page use a charting library (Chart.js, Recharts) or keep CSS-only?
2. Is there a design system/Figma file to reference for 5-layer pages?
3. Should the duplicate `onboarding.astro` be removed or kept for A/B testing?
4. What's the target browser support matrix (IE11, Safari 14, etc.)?
5. Should we add dark/light mode toggle (currently dark theme only)?

---

## Appendix: File Locations

All paths are absolute:

- Layout: `/Users/macbook/mekong-cli/packages/raas-dashboard/src/layouts/dashboard-layout.astro`
- Styles: `/Users/macbook/mekong-cli/packages/raas-dashboard/src/styles/dashboard.css`
- API Client: `/Users/macbook/mekong-cli/packages/raas-dashboard/src/scripts/api-client.ts`
- i18n: `/Users/macbook/mekong-cli/packages/raas-dashboard/src/i18n/{vi,en}.json`
- Pages: `/Users/macbook/mekong-cli/packages/raas-dashboard/src/pages/*.astro`
- Onboard Wizard: `/Users/macbook/mekong-cli/packages/raas-dashboard/public/scripts/onboard-wizard.js`
