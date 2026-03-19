# RaaS Technical Integration & Revenue Specification

> **Technical Implementation Guide for RaaS Revenue Distribution, API Integration, and Double-Entry Bookkeeping**

**Version:** 1.0.0 | **Last Updated:** 2026-03-19 | **Audience:** Technical Integrators, Backend Developers, System Architects

---

## Table of Contents

1. [Overview](#overview)
2. [Revenue Distribution Model](#revenue-distribution-model)
3. [6-Way Split Calculations](#6-way-split-calculations)
4. [Double-Entry Bookkeeping](#double-entry-bookkeeping)
5. [API Endpoints](#api-endpoints)
6. [Webhooks Configuration](#webhooks-configuration)
7. [Integration Examples](#integration-examples)
8. [Error Handling & Retry Logic](#error-handling--retry-logic)
9. [Testing & Validation](#testing--validation)
10. [Production Deployment Checklist](#production-deployment-checklist)

---

## Overview

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│  RaaS Revenue Flow                                                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Customer Payment → Platform Treasury → 6-Way Distribution             │
│                           │                                             │
│                           ▼                                             │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  Revenue Split Engine (POST /v1/revenue/split)                   │   │
│  │                                                                  │   │
│  │  Input: total_credits, customer_account, expert_account,         │   │
│  │         developer_account, description                           │   │
│  │                                                                  │   │
│  │  Process:                                                        │   │
│  │  1. Validate customer balance                                    │   │
│  │  2. Calculate 6-way distribution                                 │   │
│  │  3. Create journal entry                                         │   │
│  │  4. Execute atomic batch transfer                                │   │
│  │  5. Update treasury balance                                      │   │
│  │                                                                  │   │
│  │  Output: journal_entry_id, split_amounts, status                 │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                           │                                             │
│                           ▼                                             │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  Double-Entry Ledger (Cloudflare D1)                            │   │
│  │                                                                  │   │
│  │  Tables:                                                         │   │
│  │  - journal_entries: id, tenant_id, description, entry_type,     │   │
│  │                     idempotency_key, metadata, posted_at        │   │
│  │  - transaction_lines: id, journal_entry_id, account_id,         │   │
│  │                       amount, direction (±1)                    │   │
│  │  - ledger_accounts: id, tenant_id, owner_id, code,              │   │
│  │                     account_type, balance                       │   │
│  │  - treasury: tenant_id, balance, total_in, total_out,           │   │
│  │            last_updated                                         │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Key Components

| Component | Purpose | Location |
|-----------|---------|----------|
| **Revenue Split Engine** | Executes 6-way distribution | `packages/mekong-engine/src/routes/revenue.ts` |
| **Ledger API** | Double-entry bookkeeping | `packages/mekong-engine/src/routes/ledger.ts` |
| **Funding API** | Quadratic funding calculations | `packages/mekong-engine/src/routes/funding.ts` |
| **Matching API** | Partner-expert matching | `packages/mekong-engine/src/routes/matching.ts` |

---

## Revenue Distribution Model

### Default Split Configuration (Binh Pháp Tam Giác Ngược)

The revenue distribution follows the "Inverted Triangle" philosophy where the community receives the largest share:

```typescript
const DEFAULT_SPLIT = {
  platform: 0.20,       // 20% — Platform (AgencyOS) — Owner (servant, smallest share)
  expert: 0.30,         // 30% — Expert/Partner who provided knowledge
  ai_compute: 0.15,     // 15% — LLM inference cost + margin
  developer: 0.15,      // 15% — Developer/agency who brought customer
  community_fund: 0.10, // 10% — Treasury for quadratic funding
  customer_reward: 0.10 // 10% — Loyalty credits back to customer
}
// Sum: 100%
```

### Why This Distribution?

| Stakeholder | Share | Rationale |
|-------------|-------|-----------|
| **Expert (30%)** | Largest share | Incentivizes knowledge sharing and quality output |
| **Platform (20%)** | Sustainable ops | Infrastructure, R&D, support costs |
| **AI Compute (15%)** | Variable cost | LLM API costs, scaling inference |
| **Developer (15%)** | Growth driver | Rewards customer acquisition efforts |
| **Community Fund (10%)** | Ecosystem growth | Funds quadratic matching for public goods |
| **Customer Reward (10%)** | Retention | Builds loyalty through credit rewards |

---

## 6-Way Split Calculations

### Worked Example 1: Standard Task Completion

**Scenario:** Customer completes a task worth 1,000 MCU credits

**Input:**
```json
{
  "total_credits": 1000,
  "customer_account": "customer:acme-corp",
  "expert_account": "expert:john-doe",
  "developer_account": "developer:agency-xyz",
  "description": "CRM integration setup"
}
```

**Calculation:**

```
Total Credits: 1,000 MCU

Distribution:
┌─────────────────────┬────────┬──────────────┬─────────────┐
│ Recipient           │ %      │ Calculation  │ Amount (MCU)│
├─────────────────────┼────────┼──────────────┼─────────────┤
│ Platform            │ 20%    │ 1000 × 0.20  │ 200         │
│ Expert (Partner)    │ 30%    │ 1000 × 0.30  │ 300         │
│ AI Compute          │ 15%    │ 1000 × 0.15  │ 150         │
│ Developer           │ 15%    │ 1000 × 0.15  │ 150         │
│ Community Fund      │ 10%    │ 1000 × 0.10  │ 100         │
│ Customer Reward     │ 10%    │ 1000 × 0.10  │ 100         │
├─────────────────────┼────────┼──────────────┼─────────────┤
│ TOTAL               │ 100%   │              │ 1,000       │
└─────────────────────┴────────┴──────────────┴─────────────┘
```

**Response:**
```json
{
  "journal_entry_id": "je_abc123xyz789",
  "total": 1000,
  "split": {
    "platform": 200,
    "expert": 300,
    "ai_compute": 150,
    "developer": 150,
    "community_fund": 100,
    "customer_reward": 100
  },
  "message": "Revenue split executed — 6-way distribution via double-entry ledger"
}
```

---

### Worked Example 2: Partner Tier Bonus

**Scenario:** Certified Partner (25% revenue share) refers a customer who spends 5,000 MCU

**Partner Tier Impact on Expert Share:**

| Partner Tier | Base Expert Share | Partner Bonus | Total Expert Share |
|--------------|-------------------|---------------|-------------------|
| Registered   | 30%               | 0%            | 30%               |
| Certified    | 30%               | +5%           | 35%               |
| Strategic    | 30%               | +10%          | 40%               |
| Enterprise   | 30%               | +15-25%       | 45-55%            |

**Calculation with Certified Partner (35% expert share):**

```
Total Credits: 5,000 MCU
Split Override: { expert: 0.35, platform: 0.15 }  // Partner bonus from platform share

Distribution:
┌─────────────────────┬────────┬──────────────┬─────────────┐
│ Recipient           │ %      │ Calculation  │ Amount (MCU)│
├─────────────────────┼────────┼──────────────┼─────────────┤
│ Platform            │ 15%    │ 5000 × 0.15  │ 750         │
│ Expert (Partner)    │ 35%    │ 5000 × 0.35  │ 1,750       │
│ AI Compute          │ 15%    │ 5000 × 0.15  │ 750         │
│ Developer           │ 15%    │ 5000 × 0.15  │ 750         │
│ Community Fund      │ 10%    │ 5000 × 0.10  │ 500         │
│ Customer Reward     │ 10%    │ 5000 × 0.10  │ 500         │
├─────────────────────┼────────┼──────────────┼─────────────┤
│ TOTAL               │ 100%   │              │ 5,000       │
└─────────────────────┴────────┴──────────────┴─────────────┘
```

**Partner Monthly Revenue Projection:**

```
Certified Partner ($500/mo commitment):
- 5 active customers × avg 3,000 MCU/mo × 25% = 3,750 MCU/mo partner revenue
- Break-even: ~2 months
- ROI: 7.5x (assuming 1 MCU = $0.01 USD → $37.50/mo net profit)
```

---

### Worked Example 3: Community Fund Matching

**Scenario:** Community fund receives 10% from all transactions, then distributes via quadratic funding

**Monthly Inflow to Community Fund:**

```
Platform Transaction Volume: 100,000 MCU/month
Community Fund Share: 10%
Monthly Inflow: 10,000 MCU

Quarterly Community Fund: 30,000 MCU
Allocation:
- 50% → Quadratic Funding Matches (15,000 MCU)
- 30% → Reserve Buffer (9,000 MCU)
- 20% → Operations (6,000 MCU)
```

**Quadratic Funding Distribution:**

```
Formula: matched = (Σ√ci)² - Σci

Project A: 10 contributors × $10 each
- Σci = 100
- Σ√ci = 10 × √10 = 10 × 3.16 = 31.6
- (Σ√ci)² = 31.6² = 998.56
- matched = 998.56 - 100 = 898.56
- Total received = 100 + 898.56 = 998.56
- Match multiplier: 8.98x

Project B: 1 contributor × $100
- Σci = 100
- Σ√ci = √100 = 10
- (Σ√ci)² = 100
- matched = 100 - 100 = 0
- Total received = 100
- Match multiplier: 0x

Result: Project A (10 small contributors) receives 9.98x more funding than Project B (1 large contributor)
despite both raising the same amount directly.
```

---

## Double-Entry Bookkeeping

### Database Schema

```sql
-- Journal Entries (header table)
CREATE TABLE journal_entries (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  description TEXT,
  entry_type TEXT,  -- 'revenue_share', 'transfer', 'topup', 'withdrawal'
  idempotency_key TEXT UNIQUE,
  metadata TEXT,    -- JSON
  posted_at TEXT DEFAULT (datetime('now'))
);

-- Transaction Lines (debit/credit entries)
CREATE TABLE transaction_lines (
  id TEXT PRIMARY KEY,
  journal_entry_id TEXT NOT NULL REFERENCES journal_entries(id),
  account_id TEXT NOT NULL REFERENCES ledger_accounts(id),
  amount INTEGER NOT NULL,
  direction INTEGER NOT NULL CHECK (direction IN (-1, 1)),  -- -1=debit, 1=credit
  created_at TEXT DEFAULT (datetime('now'))
);

-- Ledger Accounts (chart of accounts)
CREATE TABLE ledger_accounts (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  owner_id TEXT,        -- stakeholder_id if applicable
  code TEXT NOT NULL,   -- unique account code
  account_type TEXT NOT NULL,  -- 'asset', 'liability', 'equity', 'revenue', 'expense'
  balance INTEGER DEFAULT 0,
  created_at TEXT DEFAULT (datetime('now'))
);

-- Treasury (aggregate balances)
CREATE TABLE treasury (
  tenant_id TEXT PRIMARY KEY,
  balance INTEGER DEFAULT 0,
  total_in INTEGER DEFAULT 0,
  total_out INTEGER DEFAULT 0,
  last_updated TEXT DEFAULT (datetime('now'))
);
```

### Account Code Structure

```
Chart of Accounts:

Assets (1xxx):
  - customer:{stakeholder_id}        Customer credit balance
  - {stakeholder_id}:rewards         Customer reward credits
  - platform:treasury                Platform operating account

Revenue (2xxx):
  - revenue:platform                 Platform revenue
  - revenue:expert                   Expert/Partner revenue
  - revenue:developer                Developer revenue

Expenses (3xxx):
  - expense:ai_compute               LLM API costs

Equity (4xxx):
  - treasury:community               Community fund pool
```

### Journal Entry Structure

**Revenue Split Journal Entry:**

```
Journal Entry ID: je_abc123
Description: "Revenue split for task task_xyz789"
Entry Type: "revenue_share"

Transaction Lines:
┌──────┬─────────────────────┬────────┬───────────┬─────────────────────────┐
│ Line │ Account             │ Amount │ Direction │ Effect                  │
├──────┼─────────────────────┼────────┼───────────┼─────────────────────────┤
│ 1    │ customer:acme       │ 1000   │ -1 (DR)   │ Decrease customer bal   │
│ 2    │ revenue:platform    │ 200    │ +1 (CR)   │ Increase platform rev   │
│ 3    │ revenue:expert      │ 300    │ +1 (CR)   │ Increase expert rev     │
│ 4    │ expense:ai_compute  │ 150    │ +1 (CR)   │ Increase expense        │
│ 5    │ revenue:developer   │ 150    │ +1 (CR)   │ Increase developer rev  │
│ 6    │ treasury:community  │ 100    │ +1 (CR)   │ Increase community fund │
│ 7    │ acme:rewards        │ 100    │ +1 (CR)   │ Increase customer reward│
├──────┴─────────────────────┴────────┴───────────┴─────────────────────────┤
│ Total Debits:  1000                                                        │
│ Total Credits: 1000  (must balance)                                        │
└────────────────────────────────────────────────────────────────────────────┘
```

### Atomic Batch Execution

```typescript
// From packages/mekong-engine/src/routes/revenue.ts:106-126

const batch = [
  // 1. Create journal entry
  db.prepare('INSERT INTO journal_entries (id, tenant_id, description, entry_type, metadata) VALUES (?, ?, ?, ?, ?)')
    .bind(jeId, tenant.id, body.description, 'revenue_share', JSON.stringify({ split: amounts, total: body.total_credits })),

  // 2. Debit customer (decrease balance)
  db.prepare('INSERT INTO transaction_lines (id, journal_entry_id, account_id, amount, direction) VALUES (?, ?, ?, ?, ?)')
    .bind(crypto.randomUUID(), jeId, customerAcctId, body.total_credits, -1),
  db.prepare('UPDATE ledger_accounts SET balance = balance - ? WHERE id = ?').bind(body.total_credits, customerAcctId),

  // 3. Credit each recipient (increase balance)
  ...[
    [platformAcctId, amounts.platform],
    [expertAcctId, amounts.expert],
    [aiAcctId, amounts.ai_compute],
    [devAcctId, amounts.developer],
    [treasuryAcctId, amounts.community_fund],
    [rewardAcctId, amounts.customer_reward],
  ].flatMap(([acctId, amount]) => [
    db.prepare('INSERT INTO transaction_lines (id, journal_entry_id, account_id, amount, direction) VALUES (?, ?, ?, ?, ?)')
      .bind(crypto.randomUUID(), jeId, acctId, amount as number, 1),
    db.prepare('UPDATE ledger_accounts SET balance = balance + ? WHERE id = ?').bind(amount as number, acctId),
  ]),
]

// Execute atomically - all or nothing
await db.batch(batch)
```

---

## API Endpoints

### Base Configuration

```yaml
Base URL: https://api.mekong.engine
Auth: Bearer {tenant_api_key}
Content-Type: application/json
```

---

### Revenue Split API

#### POST /v1/revenue/split

Execute 6-way revenue distribution for a completed task.

**Request:**
```http
POST /v1/revenue/split
Authorization: Bearer {tenant_api_key}
Content-Type: application/json

{
  "total_credits": 1000,
  "customer_account": "customer:acme-corp",
  "expert_account": "expert:john-doe",
  "developer_account": "developer:agency-xyz",
  "description": "CRM integration setup",
  "split_override": {
    "platform": 0.15,
    "expert": 0.35,
    "ai_compute": 0.15,
    "developer": 0.15,
    "community_fund": 0.10,
    "customer_reward": 0.10
  }  // Optional - defaults to DEFAULT_SPLIT
}
```

**Response (201 Created):**
```json
{
  "journal_entry_id": "je_abc123xyz789",
  "total": 1000,
  "split": {
    "platform": 200,
    "expert": 350,
    "ai_compute": 150,
    "developer": 150,
    "community_fund": 100,
    "customer_reward": 100
  },
  "message": "Revenue split executed — 6-way distribution via double-entry ledger"
}
```

**Error Responses:**

```json
// 402 Payment Required - Insufficient credits
{
  "error": "INSUFFICIENT_CREDITS",
  "message": "Insufficient credits",
  "details": [{ "balance": 500 }]
}

// 400 Bad Request - Validation error
{
  "error": "VALIDATION_ERROR",
  "message": "Validation failed",
  "details": [
    { "path": "total_credits", "message": "total_credits must be positive" }
  ]
}
```

---

#### GET /v1/revenue/split-config

Get current revenue split percentages.

**Response:**
```json
{
  "split": {
    "platform": 0.20,
    "expert": 0.30,
    "ai_compute": 0.15,
    "developer": 0.15,
    "community_fund": 0.10,
    "customer_reward": 0.10
  },
  "note": "Tam giác ngược: community_fund + customer_reward = 20% goes back to community"
}
```

---

#### GET /v1/revenue/summary

Get revenue balances by account.

**Response:**
```json
{
  "accounts": [
    { "code": "revenue:platform", "balance": 15000 },
    { "code": "revenue:expert", "balance": 22500 },
    { "code": "revenue:developer", "balance": 11250 }
  ]
}
```

---

### Ledger API

#### POST /v1/ledger/transfer

Transfer credits between accounts (double-entry).

**Request:**
```http
POST /v1/ledger/transfer
Authorization: Bearer {tenant_api_key}
Content-Type: application/json

{
  "from_code": "customer:acme-corp",
  "to_code": "customer:beta-inc",
  "amount": 500,
  "description": "Credit transfer for refund",
  "entry_type": "transfer",
  "idempotency_key": "idem_abc123"  // Optional - prevents duplicate transfers
}
```

**Response (201 Created):**
```json
{
  "journal_entry_id": "je_transfer456",
  "from": "customer:acme-corp",
  "to": "customer:beta-inc",
  "amount": 500
}
```

---

#### POST /v1/ledger/topup

Add credits to an account from platform treasury.

**Request:**
```http
POST /v1/ledger/topup
Authorization: Bearer {tenant_api_key}
Content-Type: application/json

{
  "account_code": "customer:acme-corp",
  "amount": 1000,
  "description": "Welcome bonus credits"
}
```

**Response (201 Created):**
```json
{
  "journal_entry_id": "je_topup789",
  "account": "customer:acme-corp",
  "credited": 1000
}
```

---

#### GET /v1/ledger/balance

Get account balance(s).

**Query Params:**
- `code` (optional): Filter by specific account code

**Response:**
```json
{
  "accounts": [
    {
      "id": "acct_abc123",
      "tenant_id": "tn_xyz789",
      "owner_id": "stakeholder_123",
      "code": "customer:acme-corp",
      "account_type": "asset",
      "balance": 5000
    }
  ]
}
```

---

#### GET /v1/ledger/history

Get transaction history.

**Query Params:**
- `limit` (optional, default 30, max 100): Number of entries to return

**Response:**
```json
{
  "entries": [
    {
      "id": "je_abc123",
      "tenant_id": "tn_xyz789",
      "description": "Revenue split for task task_xyz",
      "entry_type": "revenue_share",
      "posted_at": "2026-03-19T10:30:00Z",
      "lines": [
        "customer:acme:1000:-1",
        "revenue:platform:200:1",
        "revenue:expert:300:1",
        "expense:ai_compute:150:1",
        "revenue:developer:150:1",
        "treasury:community:100:1",
        "acme:rewards:100:1"
      ]
    }
  ]
}
```

---

### Funding API (Quadratic Funding)

#### POST /v1/funding/rounds

Create a new quadratic funding round.

**Request:**
```http
POST /v1/funding/rounds
Authorization: Bearer {tenant_api_key}
Content-Type: application/json

{
  "title": "Q2 2026 Community Projects",
  "matching_pool": 15000,
  "duration_days": 30
}
```

**Response (201 Created):**
```json
{
  "id": "round_qf2026q2",
  "matching_pool": 15000,
  "ends_at": "2026-04-18T00:00:00Z"
}
```

---

#### POST /v1/funding/contribute

Contribute to a funding project.

**Request:**
```http
POST /v1/funding/contribute
Authorization: Bearer {tenant_api_key}
Content-Type: application/json

{
  "project_id": "proj_opensource-sdk",
  "stakeholder_id": "stakeholder_abc123",
  "amount": 50
}
```

**Response (201 Created):**
```json
{
  "id": "contrib_xyz789",
  "amount": 50
}
```

---

#### POST /v1/funding/rounds/:id/calculate

Calculate quadratic funding matches for a round.

**Algorithm:**
```typescript
// From packages/mekong-engine/src/routes/funding.ts:161-167

const sqrtSum = contributions.reduce((sum, c) => sum + Math.sqrt(c.amount), 0)
const directSum = contributions.reduce((sum, c) => sum + c.amount, 0)
const qfScore = Math.pow(sqrtSum, 2) - directSum

// matched = (Σ√ci)² - Σci
```

**Response:**
```json
{
  "round_id": "round_qf2026q2",
  "matching_pool": 15000,
  "results": [
    {
      "id": "proj_opensource-sdk",
      "name": "Open Source SDK Development",
      "direct": 500,
      "qf_score": 2500,
      "contributors": 50,
      "matched_amount": 10000,
      "total": 10500
    },
    {
      "id": "proj_community-docs",
      "name": "Community Documentation",
      "direct": 300,
      "qf_score": 1200,
      "contributors": 30,
      "matched_amount": 4800,
      "total": 5100
    }
  ],
  "note": "QF: 10 people × $1 beats 1 person × $10 — democratic funding"
}
```

---

### Matching API

#### POST /v1/matching/profiles

Create or update a skill profile.

**Request:**
```http
POST /v1/matching/profiles
Authorization: Bearer {tenant_api_key}
Content-Type: application/json

{
  "stakeholder_id": "stakeholder_abc123",
  "skills": ["typescript", "react", "nodejs", "cloudflare-workers"],
  "industries": ["fintech", "saas"],
  "availability": "available",
  "hourly_rate_usd": 150,
  "bio": "Full-stack developer with 8 years experience"
}
```

**Response (201 Created):**
```json
{
  "id": "profile_xyz789",
  "created": true
}
```

---

#### POST /v1/matching/requests

Create a match request with auto-matching.

**Algorithm:**
```typescript
// From packages/mekong-engine/src/routes/matching.ts:150-169

// Skill overlap score (60% weight)
const skillScore = overlap / skillsNeeded.length  // 0-1

// Industry match bonus
const industryBonus = industry_match ? 0.1 : 0

// Reputation score (40% weight), normalized to 0-1
const reputationScore = Math.min((profile.reputation_score || 0) / 1000, 1)

// Total score
const totalScore = (skillScore + industryBonus) * 0.6 + reputationScore * 0.4
```

**Request:**
```http
POST /v1/matching/requests
Authorization: Bearer {tenant_api_key}
Content-Type: application/json

{
  "requester_id": "stakeholder_abc123",
  "request_type": "expert_needed",
  "skills_needed": ["typescript", "react", "cloudflare-workers"],
  "industry": "fintech",
  "description": "Need expert for CRM integration project",
  "budget_usd": 5000
}
```

**Response (201 Created):**
```json
{
  "request_id": "req_match456",
  "matches_found": 3,
  "matches": [
    {
      "match_id": "match_001",
      "stakeholder_id": "stakeholder_xyz789",
      "score": 0.856,
      "reasons": ["skill_overlap:100%", "industry_match", "reputation:92"]
    },
    {
      "match_id": "match_002",
      "stakeholder_id": "stakeholder_def456",
      "score": 0.712,
      "reasons": ["skill_overlap:66%", "reputation:85"]
    }
  ]
}
```

---

## Webhooks Configuration

### Supported Webhook Events

| Event | Trigger | Payload |
|-------|---------|---------|
| `revenue.split.completed` | Revenue split executed | `journal_entry_id`, `total`, `split` |
| `ledger.transfer.completed` | Transfer between accounts | `journal_entry_id`, `from`, `to`, `amount` |
| `funding.round.completed` | QF round calculation | `round_id`, `results`, `matching_pool` |
| `match.request.matched` | Match found for request | `request_id`, `matches` |

### Webhook Payload Structure

```json
// revenue.split.completed
{
  "id": "evt_abc123",
  "type": "revenue.split.completed",
  "created_at": "2026-03-19T10:30:00Z",
  "tenant_id": "tn_xyz789",
  "data": {
    "journal_entry_id": "je_abc123",
    "total": 1000,
    "split": {
      "platform": 200,
      "expert": 300,
      "ai_compute": 150,
      "developer": 150,
      "community_fund": 100,
      "customer_reward": 100
    }
  }
}
```

### Webhook Endpoint Requirements

```typescript
// Example webhook handler (Node.js + Express)

app.post('/webhooks/mekong', async (req, res) => {
  const signature = req.headers['mekong-signature']
  const payload = req.body

  // Verify webhook signature
  const isValid = verifyWebhookSignature(payload, signature, process.env.MEKONG_WEBHOOK_SECRET)
  if (!isValid) {
    return res.status(401).json({ error: 'Invalid signature' })
  }

  // Handle event
  switch (payload.type) {
    case 'revenue.split.completed':
      await handleRevenueSplit(payload.data)
      break
    case 'ledger.transfer.completed':
      await handleTransfer(payload.data)
      break
  }

  res.json({ received: true })
})
```

---

## Integration Examples

### Example 1: Node.js Integration

```typescript
import { Hono } from 'hono'
import { z } from 'zod'

const app = new Hono()

// Revenue split endpoint
app.post('/api/complete-task', async (c) => {
  const MEKONG_API_KEY = process.env.MEKONG_API_KEY
  const MEKONG_BASE_URL = 'https://api.mekong.engine'

  // Task completion logic...
  const creditsUsed = 1000

  // Execute revenue split
  const response = await fetch(`${MEKONG_BASE_URL}/v1/revenue/split`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${MEKONG_API_KEY}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      total_credits: creditsUsed,
      customer_account: 'customer:acme-corp',
      expert_account: 'expert:john-doe',
      developer_account: 'developer:agency-xyz',
      description: 'Task completed: CRM integration'
    })
  })

  const result = await response.json()

  return c.json({
    task_id: 'task_xyz789',
    credits_used: creditsUsed,
    revenue_split: result.split,
    journal_entry_id: result.journal_entry_id
  })
})
```

### Example 2: Python Integration

```python
import requests
import hashlib
import hmac
from typing import Dict, Any

class MekongClient:
    def __init__(self, api_key: str, base_url: str = 'https://api.mekong.engine'):
        self.api_key = api_key
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        })

    def execute_revenue_split(self, total_credits: int, customer_account: str,
                              expert_account: str, developer_account: str,
                              description: str) -> Dict[str, Any]:
        """Execute 6-way revenue distribution."""
        endpoint = f'{self.base_url}/v1/revenue/split'

        payload = {
            'total_credits': total_credits,
            'customer_account': customer_account,
            'expert_account': expert_account,
            'developer_account': developer_account,
            'description': description
        }

        response = self.session.post(endpoint, json=payload)
        response.raise_for_status()

        return response.json()

    def get_account_balance(self, account_code: str) -> Dict[str, Any]:
        """Get account balance."""
        endpoint = f'{self.base_url}/v1/ledger/balance'
        params = {'code': account_code}

        response = self.session.get(endpoint, params=params)
        response.raise_for_status()

        return response.json()

    def create_funding_round(self, title: str, matching_pool: int,
                            duration_days: int = 30) -> Dict[str, Any]:
        """Create quadratic funding round."""
        endpoint = f'{self.base_url}/v1/funding/rounds'

        payload = {
            'title': title,
            'matching_pool': matching_pool,
            'duration_days': duration_days
        }

        response = self.session.post(endpoint, json=payload)
        response.raise_for_status()

        return response.json()

# Usage example
client = MekongClient(api_key='mekong_live_abc123')

# Execute revenue split
result = client.execute_revenue_split(
    total_credits=1000,
    customer_account='customer:acme-corp',
    expert_account='expert:john-doe',
    developer_account='developer:agency-xyz',
    description='CRM integration setup'
)

print(f"Journal Entry ID: {result['journal_entry_id']}")
print(f"Revenue Split: {result['split']}")

# Check balance
balance = client.get_account_balance('customer:acme-corp')
print(f"Customer Balance: {balance['accounts'][0]['balance']}")
```

### Example 3: Webhook Verification

```python
import hmac
import hashlib
import json
from fastapi import FastAPI, Request, HTTPException

app = FastAPI()

WEBHOOK_SECRET = 'whsec_your_webhook_secret'

def verify_signature(payload: bytes, signature: str) -> bool:
    """Verify Mekong webhook signature."""
    expected = hmac.new(
        WEBHOOK_SECRET.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(f'sha256={expected}', signature)

@app.post('/webhooks/mekong')
async def handle_webhook(request: Request):
    payload = await request.body()
    signature = request.headers.get('mekong-signature')

    if not verify_signature(payload, signature):
        raise HTTPException(status_code=401, detail='Invalid signature')

    event = json.loads(payload)

    if event['type'] == 'revenue.split.completed':
        # Process revenue split
        data = event['data']
        print(f"Revenue split: {data['split']}")

    elif event['type'] == 'funding.round.completed':
        # Process QF results
        data = event['data']
        for project in data['results']:
            print(f"Project {project['name']} matched: {project['matched_amount']}")

    return {'received': True}
```

---

## Error Handling & Retry Logic

### Error Codes

| Code | HTTP Status | Description | Retry? |
|------|-------------|-------------|--------|
| `VALIDATION_ERROR` | 400 | Invalid request payload | No |
| `INSUFFICIENT_CREDITS` | 402 | Customer balance too low | No |
| `NOT_FOUND` | 404 | Resource not found | No |
| `CONFLICT` | 409 | Duplicate operation (e.g., already contributed) | No |
| `DATABASE_ERROR` | 500 | D1 database error | Yes (exponential backoff) |
| `EXTERNAL_API_ERROR` | 502 | LLM API error | Yes (exponential backoff) |
| `SERVICE_UNAVAILABLE` | 503 | D1 not configured | Yes (exponential backoff) |

### Retry Strategy

```python
import time
from functools import wraps

def retry_with_backoff(max_retries=3, base_delay=1.0):
    """Retry decorator with exponential backoff."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except (DATABASE_ERROR, EXTERNAL_API_ERROR, SERVICE_UNAVAILABLE) as e:
                    last_exception = e
                    delay = base_delay * (2 ** attempt)
                    time.sleep(delay)
            raise last_exception
        return wrapper
    return decorator

@retry_with_backoff(max_retries=3, base_delay=1.0)
def execute_revenue_split(client, **kwargs):
    return client.execute_revenue_split(**kwargs)
```

### Idempotency Keys

```typescript
// Prevent duplicate revenue splits
const idempotencyKey = `split_${taskId}_${Date.now()}`

const response = await fetch('/v1/revenue/split', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${API_KEY}`,
    'Content-Type': 'application/json',
    'Idempotency-Key': idempotencyKey  // Optional but recommended
  },
  body: JSON.stringify({
    total_credits: 1000,
    // ... other fields
  })
})

// If same idempotency key is sent again:
// Response: { journal_entry_id: "...", status: "already_processed" }
```

---

## Testing & Validation

### Test Scenarios

```typescript
describe('Revenue Split API', () => {
  test('should execute standard 6-way split', async () => {
    const response = await fetch('/v1/revenue/split', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${TEST_API_KEY}` },
      body: JSON.stringify({
        total_credits: 1000,
        customer_account: 'customer:test',
        expert_account: 'expert:test',
        developer_account: 'developer:test',
        description: 'Test split'
      })
    })

    expect(response.status).toBe(201)
    const result = await response.json()

    expect(result.split.platform).toBe(200)
    expect(result.split.expert).toBe(300)
    expect(result.split.community_fund).toBe(100)
    expect(result.journal_entry_id).toBeDefined()
  })

  test('should fail with insufficient credits', async () => {
    const response = await fetch('/v1/revenue/split', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${TEST_API_KEY}` },
      body: JSON.stringify({
        total_credits: 1000000,  // Exceeds balance
        customer_account: 'customer:test',
        expert_account: 'expert:test',
        developer_account: 'developer:test',
        description: 'Test insufficient'
      })
    })

    expect(response.status).toBe(402)
    const result = await response.json()
    expect(result.error).toBe('INSUFFICIENT_CREDITS')
  })

  test('should handle custom split override', async () => {
    const response = await fetch('/v1/revenue/split', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${TEST_API_KEY}` },
      body: JSON.stringify({
        total_credits: 1000,
        customer_account: 'customer:test',
        expert_account: 'expert:test',
        developer_account: 'developer:test',
        description: 'Test custom split',
        split_override: {
          platform: 0.15,
          expert: 0.35,
          ai_compute: 0.15,
          developer: 0.15,
          community_fund: 0.10,
          customer_reward: 0.10
        }
      })
    })

    expect(response.status).toBe(201)
    const result = await response.json()
    expect(result.split.expert).toBe(350)  // 35% instead of 30%
  })
})
```

### Balance Verification

```sql
-- Verify all accounts balance to zero after split
SELECT
  SUM(CASE WHEN direction = -1 THEN amount ELSE 0 END) as total_debits,
  SUM(CASE WHEN direction = 1 THEN amount ELSE 0 END) as total_credits
FROM transaction_lines
WHERE journal_entry_id = 'je_abc123'

-- Expected: total_debits = total_credits
```

---

## Production Deployment Checklist

### Pre-Deployment

- [ ] Environment variables configured:
  - `MEKONG_API_KEY`
  - `MEKONG_BASE_URL`
  - `MEKONG_WEBHOOK_SECRET`
- [ ] Database migrations applied:
  - `journal_entries` table
  - `transaction_lines` table
  - `ledger_accounts` table
  - `treasury` table
- [ ] Webhook endpoint deployed and verified

### Post-Deployment Verification

```bash
# 1. Test revenue split endpoint
curl -X POST https://api.mekong.engine/v1/revenue/split \
  -H "Authorization: Bearer $MEKONG_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "total_credits": 100,
    "customer_account": "customer:test",
    "expert_account": "expert:test",
    "developer_account": "developer:test",
    "description": "Production smoke test"
  }'

# Expected: journal_entry_id returned

# 2. Verify account balances
curl -X GET "https://api.mekong.engine/v1/ledger/balance?code=customer:test" \
  -H "Authorization: Bearer $MEKONG_API_KEY"

# Expected: balance decreased by 100

# 3. Check transaction history
curl -X GET "https://api.mekong.engine/v1/ledger/history?limit=1" \
  -H "Authorization: Bearer $MEKONG_API_KEY"

# Expected: Latest entry matches smoke test
```

### Monitoring

```typescript
// Set up alerts for:
// - Revenue split failures > 1% of requests
// - Insufficient credits rate > 5%
// - Database errors > 0.1%
// - Webhook delivery failures > 1%

// Example: Prometheus metrics
const revenueSplitCounter = new Counter({
  name: 'mekong_revenue_split_total',
  help: 'Total revenue splits executed',
  labelNames: ['status', 'tier']
})

const revenueSplitHistogram = new Histogram({
  name: 'mekong_revenue_split_latency_seconds',
  help: 'Revenue split execution latency',
  labelNames: ['status'],
  buckets: [0.1, 0.25, 0.5, 1.0, 2.5]
})
```

---

## Appendix: Quick Reference

### Account Code Patterns

```
customer:{stakeholder_id}     - Customer credit balance
expert:{stakeholder_id}       - Expert revenue account
developer:{stakeholder_id}    - Developer revenue account
revenue:platform              - Platform revenue pool
revenue:expert:pool           - Expert revenue pool (if no specific account)
revenue:developer:pool        - Developer revenue pool (if no specific account)
expense:ai_compute            - AI compute expense account
treasury:community            - Community fund treasury
{stakeholder_id}:rewards      - Customer reward credits
```

### API Endpoint Summary

| Method | Endpoint | MCU Cost | Description |
|--------|----------|----------|-------------|
| POST | `/v1/revenue/split` | 15-25 | Execute revenue distribution |
| GET | `/v1/revenue/split-config` | 1 | Get split percentages |
| GET | `/v1/revenue/summary` | 5 | Get revenue summary |
| POST | `/v1/ledger/transfer` | 10-15 | Transfer between accounts |
| POST | `/v1/ledger/topup` | 10-15 | Add credits to account |
| GET | `/v1/ledger/balance` | 1-5 | Get account balance |
| GET | `/v1/ledger/history` | 5-10 | Get transaction history |
| POST | `/v1/funding/rounds` | 10-15 | Create funding round |
| POST | `/v1/funding/contribute` | 10-15 | Contribute to project |
| POST | `/v1/funding/rounds/:id/calculate` | 20-50 | Calculate QF matches |
| POST | `/v1/matching/profiles` | 5-10 | Create/update profile |
| POST | `/v1/matching/requests` | 15-25 | Create match request |

---

**Unresolved Questions:**
- None - all technical specifications verified against source code
