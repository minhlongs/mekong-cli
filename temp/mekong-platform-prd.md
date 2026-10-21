# Cyber-Bento Horizon: Mekong Agent & SaaS Platform

## Product Overview

**The Pitch:** An integrated open-core developer platform and cloud control plane that combines a high-conversion public landing site, an ultra-dense real-time desktop agent cockpit, and an enterprise SaaS control plane with metered MCU billing, PayOS VietQR payments, and tamper-evident SHA-256 compliance ledgers for autonomous business operations.

**For:** Solo technical founders, SME engineering leads, and autonomous business operators in Southeast Asia who need local-first agent reliability, zero cloud lock-in, and instant fiat-to-credit monetization.

**Device:** desktop

**Design Direction:** "Cyber-Bento Horizon" — A high-density, performance-driven dark aesthetic. Deep space obsidian canvas (`#090A0F`), crisp dark slate panels (`#11131A`), subtle 1px luminous borders (`#1E2230`), and electric neon accents (`#10B981` Emerald and `#06B6D4` Cyan). Linear-level keyboard ergonomics, modular bento containers, and zero gratuitous gradients.

**Inspired by:** Linear, Vercel, Supabase, Raycast, Bloomberg Terminal, Stripe Dashboard

---

## Screens

- **Public Marketing & Hero Landing:** Interactive browser terminal demo, 60-second quickstart copyable command, live Open-Core trust badges, and modular bento capability showcase.
- **Transparent Pricing & Tier Matrix:** Interactive billing matrix comparing BASIC (MIT), PREMIUM, ENTERPRISE, and MASTER tiers with dynamic VND/MCU currency toggles and quota calculators.
- **Desktop Agent Cockpit & Swarm Topology:** Tri-column real-time console with active agent fleet monitor, live streaming execution logs, memory graph inspector, and `Cmd+K` command palette overlay.
- **Cloud Control Plane & MCU Billing Meter:** Organization workspace dashboard with real-time MCU credit burndown graph, HTTP 402 low-balance warning banner, and instant PayOS VietQR top-up modal.
- **Immutable Compliance Audit Ledger:** Tamper-evident cryptographic ledger explorer displaying SHA-256 block chains, verified transaction hashes, TT78/SOC2 filters, and audit export.
- **Strategy Recipe Marketplace & Creator Hub:** Community & enterprise strategy catalog with 1-click recipe installation, verified creator badges, revenue-share analytics, and ratings.
- **Enterprise Multi-Tenant & Key Vault:** Workspace RBAC permission manager, KMS-encrypted tenant BYOK key vault (OpenRouter, Anthropic, Zalo OA), and webhook endpoint router.
- **Component Style Guide:** Visual contract rendering every UI token in all states — buttons, input fields, bento cards, status badges, typography scales, color swatches, and spacing units.

---

## Key Flows

**Flow 1: Quickstart to PayOS VietQR Top-Up:**
1. User lands on **Public Marketing & Hero Landing**, executes the copyable `pip install mekong && mekong init` quickstart snippet, and launches the local interface.
2. User opens **Desktop Agent Cockpit & Swarm Topology**, dispatches a 4-agent C-Suite workflow, and observes live execution in the streaming terminal.
3. Upon consuming all complimentary local units, an HTTP 402 quota banner appears prompting cloud daemon synchronization.
4. User clicks "Top Up MCU" to transition to **Cloud Control Plane & MCU Billing Meter**.
5. User selects 250,000 VND (250 MCU), generating a dynamic VietQR payment modal with live polling.
6. User scans QR via banking app; PayOS webhook confirms HMAC-SHA256 signature, credits 250 MCU in SQLite ledger, and triggers a real-time confetti toast.
7. User navigates to **Immutable Compliance Audit Ledger** to inspect the cryptographically chained SHA-256 transaction record.

**Flow 2: Marketplace Recipe Purchase to Execution:**
1. User browses **Strategy Recipe Marketplace & Creator Hub**, filtering for "TT78 Tax & Accounting Funnel".
2. User previews recipe code, verified trust badge, and automated compliance guarantees.
3. User clicks "Install Recipe (50 MCU)", which deducts from their Cloud MCU balance and deploys the workflow into their local **Desktop Agent Cockpit**.
4. The Cockpit visualizes the recipe's dependency DAG in the swarm topology panel and initiates autonomous execution.

**Flow 3: Enterprise Multi-Tenant & Key Vault Provisioning:**
1. Enterprise admin navigates to **Enterprise Multi-Tenant & Key Vault**, creating a dedicated workspace for the accounting department.
2. Admin assigns RBAC roles (Admin, Operator, Auditor) and injects KMS-encrypted Zalo OA and LLM API keys.
3. Admin configures webhook forwarding endpoints and confirms all subsequent operations log immutably to the **Immutable Compliance Audit Ledger**.

---

<details>
<summary>Design System</summary>

## Color Palette

- **Background (Canvas):** `#090A0F` - Deep space obsidian base canvas
- **Surface (Card Panel):** `#11131A` - Slightly elevated dark slate container panel
- **Surface Hover:** `#181B26` - Interactive hover state for cards and rows
- **Border Subtle:** `#1E2230` - Default 1px card and bento grid borders
- **Border Active:** `#2F364A` - Focused or active element border
- **Text Primary:** `#F8FAFC` - High-contrast crisp white for headings and primary copy
- **Text Muted:** `#94A3B8` - Slate gray for secondary descriptions and labels
- **Text Dim:** `#64748B` - Subdued gray for timestamps, breadcrumbs, and hotkey hints
- **Primary Accent (Emerald):** `#10B981` - Cyber emerald for active agents, positive status, and primary CTAs
- **Secondary Accent (Cyan):** `#06B6D4` - Electric cyan for telemetry metrics, links, and code highlights
- **Warning (Amber):** `#F59E0B` - Quota warning, pending webhooks, and rate limit indicators
- **Error (Crimson):** `#EF4444` - Failed execution, invalid signature, and secret purge alerts

## Typography

- **Headings:** Inter, Semi-Bold & Bold, 20px - 36px (tight tracking `-0.02em`, clean geometry)
- **UI Labels:** Inter, Medium, 12px - 14px (crisp legibility, uppercase for metadata badges)
- **Data/Code:** JetBrains Mono, Regular & Medium, 11px - 13px (tabular figures, code blocks, hashes)

**Style notes:** 
- Border radii: `ROUND_EIGHT` (8px on outer bento cards, 6px on buttons and inner inputs).
- Shadows: Zero muddy drop shadows; only crisp 1px borders combined with subtle inner glow on focused cards.
- Keyboard ergonomics: Every interactive component displays its keyboard shortcut hint (e.g. `[Cmd+K]`, `[G then C]`).

## Design Tokens

```css
:root {
  --bg-app: #090A0F;
  --bg-panel: #11131A;
  --bg-hover: #181B26;
  --border-subtle: #1E2230;
  --border-active: #2F364A;
  --text-main: #F8FAFC;
  --text-muted: #94A3B8;
  --text-dim: #64748B;
  --color-primary: #10B981;
  --color-secondary: #06B6D4;
  --color-warning: #F59E0B;
  --color-error: #EF4444;
  --font-ui: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  --font-mono: 'JetBrains Mono', monospace;
  --radius-card: 8px;
  --radius-btn: 6px;
}
```

</details>

---

<details>
<summary>Screen Specifications</summary>

### Screen 01: Public Marketing & Hero Landing
- **Layout:** Bento-grid landing hero with split terminal simulation on top, followed by 3-column feature grid and live OSS trust metrics.
- **Key Elements:**
  - Hero headline: "The Autonomous Agent Platform for Solo Builders & SMEs".
  - Quickstart widget: 1-line copyable terminal command with dynamic typewriter animation.
  - Interactive Terminal preview: Real-time simulated execution of C-Suite dispatch and TT78 invoice validation.
  - Trust bar: GitHub stars counter, 86/86 tests green badge, and 0-leaked-keys certification badge.
  - Bento Feature Cards: "Local-First Execution", "VietQR Fiat Onramp", "Immutable SHA-256 Ledger", "Community Recipe Hub".

### Screen 02: Transparent Pricing & Tier Matrix
- **Layout:** 4-column side-by-side tier comparison with floating VND/MCU currency switch and usage slider.
- **Key Elements:**
  - Tier Cards:
    - **BASIC (0 VND/mo):** MIT Core, local CLI, BYOK adapters, community recipes.
    - **PREMIUM (490,000 VND/mo):** 500 MCU included, managed 24/7 cloud daemon, Zalo OA webhook bridge.
    - **ENTERPRISE (2,490,000 VND/mo):** 3,000 MCU, multi-tenant RBAC, KMS key vault, TT78 audit exports.
    - **MASTER (Custom):** Dedicated Cloudflare Workers, custom SLA, bespoke quantitative/banking engines.
  - Interactive Slider: Estimate monthly MCU burn based on agent fleet size and transaction volume.
  - Feature comparison matrix with sticky headers and checkmark tooltips.

### Screen 03: Desktop Agent Cockpit & Swarm Topology
- **Layout:** Tri-column developer console with top command bar (`Cmd+K`).
- **Key Elements:**
  - Left Column (Agent Swarm Fleet): Tree view of active agents (`CEO`, `CTO`, `Tax-Engine`, `PayOS-Daemon`) with pulse status dots (green = running, amber = pending, blue = verifying).
  - Center Column (Live Streaming Terminal): Dual pane with syntax-highlighted execution logs, AST verification status, and self-healing auto-repair markers.
  - Right Column (Telemetry & Memory): Real-time CPU/RAM gauges, SQLite memory entity graph, and active token counters.
  - Command Palette: Full-screen modal triggered by `Cmd+K` for instant command dispatch and navigation.

### Screen 04: Cloud Control Plane & MCU Billing Meter
- **Layout:** Header with tenant selector and balance summary; 2-column split below with billing graphs on left and PayOS VietQR checkout on right.
- **Key Elements:**
  - Balance Card: Large display of remaining MCU balance (e.g. `9,420 MCU` = `9,420,000 VND`) with 30-day burndown chart.
  - Low-Balance Banner: Ambient amber banner when balance drops below 50 MCU with 1-click "Quick Recharge".
  - VietQR Payment Card: Amount presets (100k, 250k, 500k, 1,000k VND) generating a high-resolution PayOS VietQR with real-time polling spinner.
  - Invoice & Transaction History Table: Searchable list of past top-ups, download receipt buttons, and PayOS reference IDs.

### Screen 05: Immutable Compliance Audit Ledger
- **Layout:** Full-width cryptographic ledger table with top filter toolbar and collapsible block inspector drawer.
- **Key Elements:**
  - Integrity Banner: Green badge reading "Audit Chain Verified: 1,429 Blocks Intact (Zero Tampering Detected)".
  - Ledger Table: Columns for Block #, Timestamp, Tenant ID, Event Type (`AUTH`, `DEDUCT`, `TOPUP`, `EXEC`), SHA-256 Hash, and Verification Status.
  - Block Detail Drawer: Clicking any row slides out JSON details with previous block hash, nonce, payload, and cryptographic signature.
  - Export Toolbar: Buttons to export cryptographically signed audit package in JSONL or PDF format for TT78 tax inspections.

### Screen 06: Strategy Recipe Marketplace & Creator Hub
- **Layout:** Card grid with category sidebar (Marketing, Tax, Banking, Operations, Maritime) and top search bar.
- **Key Elements:**
  - Recipe Cards: Title, author avatar, verified badge, rating (4.9/5.0), MCU price (`50 MCU`), and "1-Click Install" button.
  - Featured Spotlight: "TT78 Automated E-Invoice Generator v2.4" with performance stats and user reviews.
  - Creator Revenue Dashboard: Secondary tab showing creator earnings, monthly payouts, and recipe usage analytics.

### Screen 07: Enterprise Multi-Tenant & Key Vault
- **Layout:** Tabbed enterprise configuration: "Workspaces & RBAC", "Encrypted Key Vault", and "Webhooks".
- **Key Elements:**
  - Tenant Switcher & Organization Member List with role chips (Owner, Admin, Member, Auditor).
  - Key Vault: Masked input fields for `OPENROUTER_API_KEY`, `ANTHROPIC_API_KEY`, `PAYOS_CHECKSUM_KEY` with status indicators showing KMS encryption status.
  - Webhook Routing Table: Destination URLs, HMAC secret rotation button, and delivery retry policies.

### Screen 08: Component Style Guide
- **Layout:** Comprehensive component token catalog organized in sequential sections.
- **Key Elements:**
  - Buttons Section: Primary Emerald, Secondary Cyan, Ghost Slate, Destructive Red, Icon-only, and loading states.
  - Form Controls: Text inputs with keyboard shortcuts, dropdowns, toggle switches, and search boxes.
  - Bento Container Matrix: 1x1, 2x1, and 2x2 responsive bento card variants with subtle 1px border lighting.
  - Status Indicators: Pulsing agent status badges, hash chips, currency tags, and progress bars.
  - Color Swatches & Typography Scale: Interactive palette cards with click-to-copy hex values and live font testers.

</details>

---

<details>
<summary>Build Guide</summary>

### Stack Recommendation
- **Framework:** Next.js 15 (App Router, React 19, Server Components for audit ledger and SSR landing).
- **Styling:** Tailwind CSS v4 + Lucide React + Radix UI primitives.
- **State Management & Telemetry:** Zustand for local Cockpit state + WebSocket client for live daemon streaming.
- **Visuals & Charts:** Recharts / Tremor for MCU burndown and telemetry gauges.
- **Backend APIs:** FastAPI :8000 (Mekong Gateway) + SQLite WAL / Cloudflare Workers.

### Build Order
1. **Foundation:** Implement Component Style Guide (`Screen 08`) and Tailwind design tokens.
2. **Core Operations:** Build Desktop Agent Cockpit (`Screen 03`) with streaming WebSocket terminal.
3. **Monetization Engine:** Implement Cloud Control Plane & MCU Billing Meter (`Screen 04`) with PayOS VietQR modal.
4. **Governance & Compliance:** Build Immutable Compliance Audit Ledger (`Screen 05`) with SHA-256 chain inspector.
5. **Growth & Distribution:** Build Public Marketing Landing (`Screen 01`) and Transparent Pricing (`Screen 02`).
6. **Ecosystem & Enterprise:** Complete Strategy Recipe Marketplace (`Screen 06`) and Enterprise Key Vault (`Screen 07`).

</details>
