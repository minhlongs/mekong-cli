# RaaS Revenue Distribution Model

> **Binh Pháp Tam Giác Ngược** — "Inverted Triangle": Community gets most value, platform serves as servant leader.

**Version:** 1.0.0 | **Last Updated:** 2026-03-19

---

## Executive Summary

The Revenue-as-a-Service (RaaS) platform implements a **6-way revenue distribution model** that aligns incentives across all stakeholders in the ecosystem. Unlike traditional SaaS models where the platform captures 80-100% of revenue, RaaS distributes value to:

1. **Platform (20%)** — Infrastructure, R&D, support
2. **Expert/Partner (30%)** — Referral and enablement value
3. **AI Compute (15%)** — LLM inference costs + margin
4. **Developer Fund (15%)** — Open source contributors
5. **Community Fund (10%)** — Quadratic funding pool
6. **Customer Reward (10%)** — Loyalty credits back to customer

---

## 6-Way Split Model

### Standard Distribution

| Stakeholder | Share | Share Type | Account Code |
|-------------|-------|------------|--------------|
| Platform (AgencyOS) | 20% | Revenue | `revenue:platform` |
| Expert/Partner | 30% | Revenue | `revenue:expert` |
| AI Compute | 15% | Expense | `expense:ai_compute` |
| Developer Fund | 15% | Revenue | `revenue:developer` |
| Community Fund | 10% | Equity | `treasury:community` |
| Customer Reward | 10% | Asset (liability) | `customer:rewards` |

### Philosophy: Tam Giác Ngược (Inverted Triangle)

Traditional SaaS:
```
Platform:     ████████████████████ 80-100%
Partners:     ████ 0-20%
Community:    ░░░░ 0%
```

RaaS Inverted Triangle:
```
Platform:     ████████ 20% (servant leader)
Experts:      ██████████ 30% (knowledge providers)
Ecosystem:    ████████████ 40% (dev + community + customer)
AI Costs:     █████ 15% (infrastructure)
```

**Why this works:**
- Platform is incentivized to maximize **ecosystem value**, not extract rent
- Partners earn more than platform → strong referral network
- Community fund enables quadratic funding → democratic resource allocation
- Customer rewards → loyalty and retention

---

## Calculation Examples

### Example 1: Standard Revenue Split (1,000 MCU)

**Scenario:** Customer spends 1,000 MCU on a RaaS task completion.

**Input:**
```json
{
  "total_credits": 1000,
  "customer_account": "customer:acme-corp",
  "expert_account": "expert:john-doe-uuid",
  "developer_account": "developer:agency-xyz-uuid",
  "description": "CRM integration task completion"
}
```

**Calculation:**
```
Total Credits: 1,000 MCU

Distribution:
┌─────────────────────┬───────┬───────────┬────────────────────────┐
│ Stakeholder         │ %     │ Amount    │ Account Type           │
├─────────────────────┼───────┼───────────┼────────────────────────┤
│ Platform            │ 20%   │ 200 MCU   │ Revenue                │
│ Expert (Partner)    │ 30%   │ 300 MCU   │ Revenue                │
│ AI Compute          │ 15%   │ 150 MCU   │ Expense                │
│ Developer Fund      │ 15%   │ 150 MCU   │ Revenue                │
│ Community Fund      │ 10%   │ 100 MCU   │ Equity (Treasury)      │
│ Customer Reward     │ 10%   │ 100 MCU   │ Asset (Loyalty Credit) │
└─────────────────────┴───────┴───────────┴────────────────────────┘

Verification: 200 + 300 + 150 + 150 + 100 + 100 = 1,000 MCU ✓
```

**Double-Entry Journal:**
```
Journal Entry ID: je_abc123

Debits (-1):
  customer:acme-corp                    1,000 MCU

Credits (+1):
  revenue:platform                        200 MCU
  revenue:expert                          300 MCU
  expense:ai_compute                      150 MCU
  revenue:developer                       150 MCU
  treasury:community                      100 MCU
  customer:acme-corp:rewards              100 MCU
                      ─────────────────────────────
                      Total Credits:    1,000 MCU ✓
```

---

### Example 2: Partner Tier Bonus

Partners earn different percentages based on their tier:

| Tier | Base Share | Bonus | Total Share | Requirements |
|------|------------|-------|-------------|--------------|
| Registered | 30% | 0% | 30% | Free, anyone can join |
| Certified | 30% | +5% | 35% | $500/mo, certified training |
| Strategic | 30% | +10% | 40% | $2,000/mo, SLA agreement |
| Enterprise | 30% | +15-20% | 45-50% | Custom, revenue commitment |

**Bonus Source:** Platform share is reduced to fund partner bonuses (servant leadership model).

**Scenario:** Certified Partner ($500/mo) generates 2,000 MCU in customer spend.

**Calculation:**
```
Total Credits: 2,000 MCU
Partner Tier: Certified (+5% bonus)

Adjusted Distribution:
┌─────────────────────┬───────┬───────────┬────────────────────────┐
│ Stakeholder         │ %     │ Amount    │ Notes                  │
├─────────────────────┼───────┼───────────┼────────────────────────┤
│ Platform            │ 15%   │ 300 MCU   │ Reduced by 5% bonus    │
│ Expert (Partner)    │ 35%   │ 700 MCU   │ Base 30% + 5% bonus    │
│ AI Compute          │ 15%   │ 300 MCU   │ Unchanged              │
│ Developer Fund      │ 15%   │ 300 MCU   │ Unchanged              │
│ Community Fund      │ 10%   │ 200 MCU   │ Unchanged              │
│ Customer Reward     │ 10%   │ 200 MCU   │ Unchanged              │
└─────────────────────┴───────┴───────────┴────────────────────────┘

Verification: 300 + 700 + 300 + 300 + 200 + 200 = 2,000 MCU ✓
```

**Partner Economics:**
```
Certified Partner Monthly:
  Revenue Share: 700 MCU × $0.10/MCU = $70
  Membership Fee: -$500
  Net: -$430 (investment phase)

  BUT: Partner closes 20 deals/month:
  Revenue Share: 14,000 MCU × $0.10 = $1,400
  Membership Fee: -$500
  Net: +$900/month ( profitable at scale)
```

---

### Example 3: Community Fund Matching (Quadratic Funding)

The Community Fund (10% of all revenue) is allocated via **quadratic funding**:

**Formula:**
```
matched = (Σ√ci)² - Σci

Where:
  ci = individual contribution amount
  Σ√ci = sum of square roots of contributions
  (Σ√ci)² = square of the sum
  Σci = sum of contributions (direct funding)
```

**Why Quadratic Funding?**
- Democratic allocation: many small contributions > one large contribution
- Prevents capture by wealthy stakeholders
- Aligns with "community owns the platform" philosophy

**Scenario:** Community fund has 10,000 MCU available. Three projects receive individual contributions:

```
Project A: 100 contributors × 10 MCU = 1,000 MCU
Project B: 10 contributors × 100 MCU = 1,000 MCU
Project C: 1 contributor × 1,000 MCU = 1,000 MCU

Direct funding is equal (1,000 MCU each), but quadratic funding differs:

Project A:
  Σ√ci = 100 × √10 = 100 × 3.16 = 316
  (Σ√ci)² = 316² = 99,856
  Σci = 1,000
  Matched = 99,856 - 1,000 = 98,856 MCU
  Total = 1,000 + 98,856 = 99,856 MCU

Project B:
  Σ√ci = 10 × √100 = 10 × 10 = 100
  (Σ√ci)² = 100² = 10,000
  Σci = 1,000
  Matched = 10,000 - 1,000 = 9,000 MCU
  Total = 1,000 + 9,000 = 10,000 MCU

Project C:
  Σ√ci = 1 × √1000 = 31.6
  (Σ√ci)² = 31.6² = 1,000
  Σci = 1,000
  Matched = 1,000 - 1,000 = 0 MCU
  Total = 1,000 + 0 = 1,000 MCU
```

**Result:**
```
┌───────────┬────────────┬──────────────┬───────────┬─────────────┐
│ Project   │ Direct (∑) │ Matched (QF) │ Total     │ Contributors│
├───────────┼────────────┼──────────────┼───────────┼─────────────┤
│ A         │ 1,000 MCU  │ 98,856 MCU   │ 99,856 MCU│ 100         │
│ B         │ 1,000 MCU  │ 9,000 MCU    │ 10,000 MCU│ 10          │
│ C         │ 1,000 MCU  │ 0 MCU        │ 1,000 MCU │ 1           │
└───────────┴────────────┴──────────────┴───────────┴─────────────┘

Lesson: Many small contributions are rewarded 10x-100x over large single contributions.
```

---

### Example 4: Developer Fund Allocation

The Developer Fund (15% of revenue) rewards open source contributors:

**Allocation Formula:**
```
developer_share = total_credits × 0.15

Per contributor:
  contributor_share = developer_share × (contributor_score / total_score)

Where:
  contributor_score = Σ (commits × weight_commit + prs_merged × weight_pr + issues_resolved × weight_issue)
  total_score = Σ all_contributor_scores
```

**Default Weights:**
```typescript
const WEIGHTS = {
  commit: 1,        // 1 point per commit
  pr_merged: 5,     // 5 points per merged PR
  issue_resolved: 3, // 3 points per resolved issue
  bug_fix: 2,       // 2 points per bug fix
  feature: 4,       // 4 points per feature
  documentation: 1, // 1 point per doc PR
}
```

**Scenario:** Developer Fund has 3,000 MCU for the month. Three contributors:

```
Contributor A:
  50 commits × 1 = 50
  5 PRs merged × 5 = 25
  10 issues resolved × 3 = 30
  Total Score: 105

Contributor B:
  20 commits × 1 = 20
  8 PRs merged × 5 = 40
  5 issues resolved × 3 = 15
  2 bug fixes × 2 = 4
  Total Score: 79

Contributor C:
  100 commits × 1 = 100
  2 PRs merged × 5 = 10
  0 issues resolved × 3 = 0
  Total Score: 110

Total Score: 105 + 79 + 110 = 294

Distribution:
┌───────────────┬───────────┬──────────────┬──────────────────────┐
│ Contributor   │ Score     │ Share %      │ Allocation (MCU)     │
├───────────────┼───────────┼──────────────┼──────────────────────┤
│ A             │ 105       │ 35.7%        │ 1,071 MCU            │
│ B             │ 79        │ 26.9%        │ 807 MCU              │
│ C             │ 110       │ 37.4%        │ 1,122 MCU            │
└───────────────┴───────────┴──────────────┴──────────────────────┘

Verification: 1,071 + 807 + 1,122 = 3,000 MCU ✓
```

---

### Example 5: Customer Reward Loyalty Program

Customer Rewards (10% of spend) accumulate as loyalty credits:

**Rules:**
- 10% of every transaction returns to customer as credits
- Credits can be used for future RaaS tasks
- Credits expire after 12 months (to encourage usage)
- Credits are non-transferable

**Scenario:** Customer spends over 6 months:

```
Month 1: Spend 5,000 MCU → Reward 500 MCU (Balance: 500)
Month 2: Spend 8,000 MCU → Reward 800 MCU (Balance: 1,300)
Month 3: Spend 6,000 MCU → Reward 600 MCU (Balance: 1,900)
Month 4: Spend 12,000 MCU → Reward 1,200 MCU (Balance: 3,100)
Month 5: Spend 10,000 MCU → Reward 1,000 MCU (Balance: 4,100)
Month 6: Spend 15,000 MCU → Reward 1,500 MCU (Balance: 5,600)

Total Spend: 56,000 MCU
Total Rewards: 5,600 MCU (exactly 10%)
Effective Discount: 10%

Customer can use 5,600 MCU credits in Month 7+ for:
  - New feature requests
  - Rush job premiums
  - Premium expert consultations
  - Training and onboarding
```

**Business Impact:**
```
Without Rewards:
  Customer LTV: 56,000 MCU
  Churn Risk: High (no switching cost)

With Rewards:
  Customer LTV: 56,000 MCU (initial) + 20,000 MCU (redeemed credits)
  Churn Risk: Low (5,600 MCU "locked in")
  Effective Revenue: 56,000 - 5,600 = 50,400 MCU (but higher retention)
```

---

## API Implementation

### POST /revenue/split

```typescript
// packages/mekong-engine/src/routes/revenue.ts

const DEFAULT_SPLIT = {
  platform: 0.20,       // 20% — Platform
  expert: 0.30,         // 30% — Expert/Partner
  ai_compute: 0.15,     // 15% — LLM inference
  developer: 0.15,      // 15% — Developer fund
  community_fund: 0.10, // 10% — Quadratic funding
  customer_reward: 0.10 // 10% — Customer loyalty
}

// Request
POST /revenue/split
Content-Type: application/json
Authorization: Bearer <tenant_token>

{
  "total_credits": 1000,
  "customer_account": "customer:acme-corp",
  "expert_account": "expert:john-doe-uuid",
  "developer_account": "developer:agency-xyz-uuid",
  "description": "CRM integration task completion",
  "split_override": null // Optional: override default percentages
}

// Response (201 Created)
{
  "journal_entry_id": "je_abc123",
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

### Atomic Batch Execution

```typescript
const batch = [
  // 1. Create journal entry
  db.prepare('INSERT INTO journal_entries (...)').bind(jeId, tenant.id, description, 'revenue_share', metadata),

  // 2. Debit customer account
  db.prepare('INSERT INTO transaction_lines (...)').bind(uuid(), jeId, customerAcctId, total, -1),
  db.prepare('UPDATE ledger_accounts SET balance = balance - ? WHERE id = ?').bind(total, customerAcctId),

  // 3. Credit each recipient (atomic)
  ...[
    [platformAcctId, amounts.platform],
    [expertAcctId, amounts.expert],
    [aiAcctId, amounts.ai_compute],
    [devAcctId, amounts.developer],
    [treasuryAcctId, amounts.community_fund],
    [rewardAcctId, amounts.customer_reward],
  ].flatMap(([acctId, amount]) => [
    db.prepare('INSERT INTO transaction_lines (...)').bind(uuid(), jeId, acctId, amount, 1),
    db.prepare('UPDATE ledger_accounts SET balance = balance + ? WHERE id = ?').bind(amount, acctId),
  ]),
]

await db.batch(batch) // All-or-nothing execution
```

---

## Database Schema

### Journal Entries

```sql
CREATE TABLE journal_entries (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  description TEXT NOT NULL,
  entry_type TEXT NOT NULL, -- 'revenue_share', 'transfer', 'adjustment'
  metadata TEXT, -- JSON blob
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (tenant_id) REFERENCES tenants(id)
);
```

### Transaction Lines

```sql
CREATE TABLE transaction_lines (
  id TEXT PRIMARY KEY,
  journal_entry_id TEXT NOT NULL,
  account_id TEXT NOT NULL,
  amount INTEGER NOT NULL, -- Stored in smallest unit (MCU, not credits)
  direction INTEGER NOT NULL, -- -1 = debit, +1 = credit
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (journal_entry_id) REFERENCES journal_entries(id),
  FOREIGN KEY (account_id) REFERENCES ledger_accounts(id)
);

-- Index for fast balance queries
CREATE INDEX idx_transaction_lines_account ON transaction_lines(account_id);
```

### Ledger Accounts

```sql
CREATE TABLE ledger_accounts (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  code TEXT NOT NULL, -- e.g., 'revenue:platform', 'customer:acme-corp'
  account_type TEXT NOT NULL, -- 'asset', 'liability', 'equity', 'revenue', 'expense'
  balance INTEGER DEFAULT 0, -- Running balance
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (tenant_id) REFERENCES tenants(id),
  UNIQUE(tenant_id, code)
);
```

---

## Audit Trail

Every revenue split creates an immutable audit trail:

```
1. Journal Entry
   └─> Unique ID: je_abc123
   └─> Description: "CRM integration task completion"
   └─> Type: "revenue_share"
   └─> Metadata: {"split": {...}, "total": 1000}

2. Transaction Lines (6 lines)
   ├─> Line 1: Debit customer 1,000 MCU
   ├─> Line 2: Credit platform 200 MCU
   ├─> Line 3: Credit expert 300 MCU
   ├─> Line 4: Credit AI compute 150 MCU
   ├─> Line 5: Credit developer 150 MCU
   ├─> Line 6: Credit community fund 100 MCU
   └─> Line 7: Credit customer rewards 100 MCU

3. Account Balance Updates (7 updates)
   ├─> customer:acme-corp: -1,000 MCU
   ├─> revenue:platform: +200 MCU
   ├─> revenue:expert: +300 MCU
   ├─> expense:ai_compute: +150 MCU
   ├─> revenue:developer: +150 MCU
   ├─> treasury:community: +100 MCU
   └─> customer:acme-corp:rewards: +100 MCU

4. Treasury Table Update
   └─> community_fund: balance +100, total_in +100
```

**Verification Query:**
```sql
-- Verify journal entry balances (debits = credits)
SELECT
  journal_entry_id,
  SUM(CASE WHEN direction = -1 THEN amount ELSE 0 END) as total_debits,
  SUM(CASE WHEN direction = 1 THEN amount ELSE 0 END) as total_credits
FROM transaction_lines
WHERE journal_entry_id = 'je_abc123'
GROUP BY journal_entry_id;

-- Expected: total_debits = total_credits = 1,000 MCU
```

---

## Related Documents

- [RaaS Partnership Process](../raas-partnership-process.md) — Partner tiers, onboarding, revenue sharing
- [Technical Integration Spec](../technical/raas-integration-spec.md) — API endpoints, webhooks, code samples
- [Quadratic Funding](../technical/raas-integration-spec.md#quadratic-funding) — Mathematical formula and implementation
- [Double-Entry Bookkeeping](./bookkeeping-data.csv) — CSV examples of journal entries

---

## Appendix: Split Configuration

### Default Split (Code)

```typescript
// packages/mekong-engine/src/routes/revenue.ts:13-20

const DEFAULT_SPLIT = {
  platform: 0.20,       // 20% — Owner (servant, smallest share)
  expert: 0.30,          // 30% — Expert who provided knowledge
  ai_compute: 0.15,      // 15% — LLM inference cost + margin
  developer: 0.15,       // 15% — Developer/agency who brought customer
  community_fund: 0.10,  // 10% — Treasury for quadratic funding
  customer_reward: 0.10, // 10% — Loyalty credits back to customer
}
```

### Override Example

```typescript
// Custom split for enterprise partner (40% share)
const enterpriseSplit = {
  platform: 0.10,       // Reduced to 10%
  expert: 0.40,         // Enterprise partner gets 40%
  ai_compute: 0.15,     // Unchanged
  developer: 0.15,      // Unchanged
  community_fund: 0.10, // Unchanged
  customer_reward: 0.10 // Unchanged
}

// Verify: 0.10 + 0.40 + 0.15 + 0.15 + 0.10 + 0.10 = 1.00 ✓
```
