# Ledger API — Double-Entry Accounting

> **Purpose**: Hệ thống kế toán kép (double-entry accounting) với journal entries và transfers.

---

## Endpoints Overview

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/v1/ledger/transfer` | ✅ | Transfer between accounts |
| POST | `/v1/ledger/topup` | ✅ | Topup from platform treasury |
| GET | `/v1/ledger/balance` | ✅ | Get account balances |
| GET | `/v1/ledger/history` | ✅ | Transaction history |

---

## POST /v1/ledger/transfer — Double-Entry Transfer

### Request

```bash
curl -X POST https://agencyos.network/v1/ledger/transfer \
  -H "Authorization: Bearer $RAAS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "from_code": "ACCT-USER-001",
    "to_code": "ACCT-PLATFORM-001",
    "amount": 199000,
    "currency": "VND",
    "description": "Payment for tier_starter",
    "metadata": {
      "payment_id": "pay_abc123",
      "tier_id": "tier_starter"
    }
  }'
```

### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `from_code` | string | ✅ | Source account code |
| `to_code` | string | ✅ | Destination account code |
| `amount` | integer | ✅ | Amount in smallest currency unit |
| `currency` | string | ❌ | `VND` or `USD` (default: `VND`) |
| `description` | string | ❌ | Transfer description |
| `metadata` | object | ❌ | Additional data (payment_id, etc.) |

### Account Code Format

| Pattern | Description | Example |
|---------|-------------|---------|
| `ACCT-USER-{id}` | User/tenant accounts | `ACCT-USER-001` |
| `ACCT-PLATFORM-{id}` | Platform treasury | `ACCT-PLATFORM-001` |
| `ACCT-REVENUE-{type}` | Revenue accounts | `ACCT-REVENUE-SUBSCRIPTION` |
| `ACCT-EXPENSE-{type}` | Expense accounts | `ACCT-EXPENSE-PAYOUT` |
| `ACCT-CREDIT-{id}` | Credit balance accounts | `ACCT-CREDIT-001` |

### Response (201 Created)

```json
{
  "transfer_id": "xfer_abc123",
  "journal_id": "journal_xyz789",
  "status": "completed",
  "from_account": {
    "code": "ACCT-USER-001",
    "name": "Tenant #001 Operating Account",
    "balance_before": 500000,
    "balance_after": 301000
  },
  "to_account": {
    "code": "ACCT-PLATFORM-001",
    "name": "Platform Treasury",
    "balance_before": 10000000,
    "balance_after": 10199000
  },
  "amount": 199000,
  "currency": "VND",
  "description": "Payment for tier_starter",
  "metadata": {
    "payment_id": "pay_abc123",
    "tier_id": "tier_starter"
  },
  "created_at": "2026-03-19T10:30:00Z"
}
```

### Transfer Response Object

| Field | Type | Description |
|-------|------|-------------|
| `transfer_id` | string | Unique transfer ID |
| `journal_id` | string | Associated journal entry ID |
| `status` | string | `completed`, `failed`, `pending` |
| `from_account` | object | Source account details |
| `to_account` | object | Destination account details |
| `amount` | integer | Transfer amount |
| `currency` | string | Currency code |
| `description` | string | Transfer description |
| `metadata` | object | Custom metadata |
| `created_at` | string | ISO 8601 timestamp |

### Account Balance Object

| Field | Type | Description |
|-------|------|-------------|
| `code` | string | Account code |
| `name` | string | Account display name |
| `balance_before` | integer | Balance before transfer |
| `balance_after` | integer | Balance after transfer |

### Double-Entry Journal

Each transfer creates a journal entry with 2 lines:

```
┌─────────────────────────────────────────────────────────────┐
│  Journal Entry: journal_xyz789                             │
├─────────────────────────────────────────────────────────────┤
│  Line 1: DEBIT                                             │
│    Account: ACCT-PLATFORM-001 (Platform Treasury)          │
│    Amount: 199,000 VND                                     │
├─────────────────────────────────────────────────────────────┤
│  Line 2: CREDIT                                            │
│    Account: ACCT-USER-001 (Tenant #001)                    │
│    Amount: 199,000 VND                                     │
├─────────────────────────────────────────────────────────────┤
│  Total Debits: 199,000 VND                                 │
│  Total Credits: 199,000 VND                                │
│  ✓ Balanced (debits = credits)                             │
└─────────────────────────────────────────────────────────────┘
```

### Error Responses

**400 Insufficient Balance:**
```json
{
  "error": "INSUFFICIENT_BALANCE",
  "message": "Account ACCT-USER-001 has insufficient balance",
  "details": {
    "account_code": "ACCT-USER-001",
    "current_balance": 100000,
    "required_amount": 199000
  }
}
```

**400 Invalid Account:**
```json
{
  "error": "INVALID_ACCOUNT",
  "message": "Account not found: 'ACCT-INVALID-999'"
}
```

**400 Same Account:**
```json
{
  "error": "VALIDATION_ERROR",
  "message": "Cannot transfer from and to the same account"
}
```

---

## POST /v1/ledger/topup — Treasury Topup

### Purpose

Cộng credits vào tài khoản từ platform treasury (thường dùng sau khi user mua credits qua payment gateway).

### Request

```bash
curl -X POST https://agencyos.network/v1/ledger/topup \
  -H "Authorization: Bearer $RAAS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "account_code": "ACCT-CREDIT-001",
    "amount": 50,
    "currency": "CREDITS",
    "description": "Purchase tier_starter via MoMo",
    "metadata": {
      "payment_id": "pay_abc123",
      "tier_id": "tier_starter",
      "gateway": "momo"
    }
  }'
```

### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `account_code` | string | ✅ | Account to credit |
| `amount` | integer | ✅ | Amount to add |
| `currency` | string | ❌ | `CREDITS`, `VND`, `USD` |
| `description` | string | ❌ | Topup description |
| `metadata` | object | ❌ | Payment details |

### Response (201 Created)

```json
{
  "topup_id": "topup_abc123",
  "journal_id": "journal_def456",
  "status": "completed",
  "account": {
    "code": "ACCT-CREDIT-001",
    "name": "Tenant #001 Credit Balance",
    "balance_before": 10,
    "balance_after": 60
  },
  "amount": 50,
  "currency": "CREDITS",
  "description": "Purchase tier_starter via MoMo",
  "metadata": {
    "payment_id": "pay_abc123",
    "tier_id": "tier_starter",
    "gateway": "momo"
  },
  "created_at": "2026-03-19T10:30:00Z"
}
```

### Topup Flow from Payment

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Payment    │     │  Platform   │     │  Ledger     │     │  Tenant     │
│  Gateway    │ →   │  Webhook    │ →   │  API        │ →   │  Credits    │
│  (MoMo/     │     │  receives   │     │  creates    │     │  added to   │
│  VNPAY)     │     │  confirm    │     │  topup      │     │  account    │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
```

### Journal Entry for Topup

```
┌─────────────────────────────────────────────────────────────┐
│  Journal Entry: journal_def456                             │
├─────────────────────────────────────────────────────────────┤
│  Line 1: DEBIT                                             │
│    Account: ACCT-CREDIT-001 (Tenant Credit Balance)        │
│    Amount: 50 CREDITS                                      │
├─────────────────────────────────────────────────────────────┤
│  Line 2: CREDIT                                            │
│    Account: ACCT-TREASURY-CREDITS (Platform Treasury)      │
│    Amount: 50 CREDITS                                      │
├─────────────────────────────────────────────────────────────┤
│  ✓ Balanced                                                │
└─────────────────────────────────────────────────────────────┘
```

---

## GET /v1/ledger/balance — Account Balances

### Request

```bash
curl -X GET "https://agencyos.network/v1/ledger/balance?account_code=ACCT-CREDIT-001" \
  -H "Authorization: Bearer $RAAS_API_KEY"
```

### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `account_code` | string | ❌ | Filter by specific account |
| `currency` | string | ❌ | Filter by currency: `VND`, `USD`, `CREDITS` |

### Response (200 OK)

**Single Account:**
```json
{
  "account": {
    "code": "ACCT-CREDIT-001",
    "name": "Tenant #001 Credit Balance",
    "type": "asset",
    "currency": "CREDITS"
  },
  "balance": {
    "current": 60,
    "available": 60,
    "pending": 0,
    "reserved": 0
  },
  "updated_at": "2026-03-19T10:30:00Z"
}
```

**All Accounts:**
```json
{
  "accounts": [
    {
      "code": "ACCT-CREDIT-001",
      "name": "Tenant #001 Credit Balance",
      "currency": "CREDITS",
      "balance": {
        "current": 60,
        "available": 60,
        "pending": 0,
        "reserved": 0
      }
    },
    {
      "code": "ACCT-USER-001",
      "name": "Tenant #001 Operating Account",
      "currency": "VND",
      "balance": {
        "current": 301000,
        "available": 301000,
        "pending": 0,
        "reserved": 0
      }
    }
  ],
  "total_accounts": 2
}
```

### Balance Object

| Field | Type | Description |
|-------|------|-------------|
| `current` | integer | Total balance |
| `available` | integer | Available for withdrawal/spending |
| `pending` | integer | Pending transactions |
| `reserved` | integer | Reserved/frozen amount |

---

## GET /v1/ledger/history — Transaction History

### Request

```bash
curl -X GET "https://agencyos.network/v1/ledger/history?account_code=ACCT-CREDIT-001&limit=20" \
  -H "Authorization: Bearer $RAAS_API_KEY"
```

### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `account_code` | string | ❌ | Filter by account |
| `journal_id` | string | ❌ | Filter by journal entry |
| `type` | string | ❌ | `transfer`, `topup`, `debit`, `credit` |
| `limit` | integer | ❌ | Max results (default: 50, max: 100) |
| `offset` | integer | ❌ | Pagination offset |

### Response (200 OK)

```json
{
  "transactions": [
    {
      "id": "txn_001",
      "journal_id": "journal_def456",
      "type": "topup",
      "account_code": "ACCT-CREDIT-001",
      "counterparty_code": "ACCT-TREASURY-CREDITS",
      "amount": 50,
      "currency": "CREDITS",
      "direction": "credit",
      "balance_after": 60,
      "description": "Purchase tier_starter via MoMo",
      "metadata": {
        "payment_id": "pay_abc123",
        "tier_id": "tier_starter"
      },
      "created_at": "2026-03-19T10:30:00Z"
    },
    {
      "id": "txn_002",
      "journal_id": "journal_ghi789",
      "type": "transfer",
      "account_code": "ACCT-CREDIT-001",
      "counterparty_code": "ACCT-USAGE-001",
      "amount": 5,
      "currency": "CREDITS",
      "direction": "debit",
      "balance_after": 55,
      "description": "Content generation (7 days)",
      "metadata": {
        "agent": "content-writer",
        "operation": "generate_7_days"
      },
      "created_at": "2026-03-19T11:00:00Z"
    }
  ],
  "total": 47,
  "limit": 20,
  "offset": 0
}
```

### Transaction Object

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique transaction ID |
| `journal_id` | string | Parent journal entry ID |
| `type` | string | `transfer`, `topup`, `debit`, `credit` |
| `account_code` | string | Account involved in transaction |
| `counterparty_code` | string | Other account in transaction |
| `amount` | integer | Transaction amount |
| `currency` | string | Currency code |
| `direction` | string | `debit` (out) or `credit` (in) |
| `balance_after` | integer | Account balance after transaction |
| `description` | string | Transaction description |
| `metadata` | object | Custom data |
| `created_at` | string | ISO 8601 timestamp |

---

## Journal Entry Structure

### Anatomy of a Journal Entry

```
Journal Entry: journal_xyz789
Description: Payment for tier_starter
Status: completed

┌──────┬─────────────────────────┬───────────┬─────────────┬──────────────┐
│ Line │ Account                 │ Type      │ Debit (VND) │ Credit (VND) │
├──────┼─────────────────────────┼───────────┼─────────────┼──────────────┤
│ 1    │ ACCT-PLATFORM-001       │ Asset     │ 199,000     │ 0            │
│ 2    │ ACCT-USER-001           │ Asset     │ 0           │ 199,000      │
├──────┼─────────────────────────┼───────────┼─────────────┼──────────────┤
│      │ TOTALS                  │           │ 199,000     │ 199,000      │
└──────┴─────────────────────────┴───────────┴─────────────┴──────────────┘
✓ Balanced (total debits = total credits)
```

### Account Types

| Type | Normal Balance | Description |
|------|----------------|-------------|
| `asset` | Debit | Resources owned (cash, credits) |
| `liability` | Credit | Obligations owed |
| `equity` | Credit | Owner's equity |
| `revenue` | Credit | Income earned |
| `expense` | Debit | Costs incurred |

---

## Use Cases

### User Purchases Credits via MoMo

```bash
# Step 1: Payment webhook confirms success
# Step 2: Topup credits to user account
curl -X POST https://agencyos.network/v1/ledger/topup \
  -H "Authorization: Bearer $RAAS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "account_code": "ACCT-CREDIT-001",
    "amount": 50,
    "currency": "CREDITS",
    "description": "Purchase tier_starter via MoMo",
    "metadata": {
      "payment_id": "pay_abc123",
      "tier_id": "tier_starter",
      "gateway": "momo"
    }
  }'

# Result: User credit balance 10 → 60 credits
```

### Platform Collects Revenue

```bash
# Transfer from user to platform (revenue recognition)
curl -X POST https://agencyos.network/v1/ledger/transfer \
  -H "Authorization: Bearer $RAAS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "from_code": "ACCT-USER-001",
    "to_code": "ACCT-REVENUE-SUBSCRIPTION",
    "amount": 199000,
    "currency": "VND",
    "description": "Revenue from tier_starter subscription"
  }'

# Journal Entry:
# DEBIT:  ACCT-REVENUE-SUBSCRIPTION  199,000 VND
# CREDIT: ACCT-USER-001              199,000 VND
```

### Revenue Distribution to Stakeholders

```bash
# Distribute revenue to stakeholder accounts
curl -X POST https://agencyos.network/v1/ledger/transfer \
  -H "Authorization: Bearer $RAAS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "from_code": "ACCT-REVENUE-SUBSCRIPTION",
    "to_code": "ACCT-PAYOUT-FOUNDER",
    "amount": 99500,
    "currency": "VND",
    "description": "50% revenue share to founder",
    "metadata": {
      "stakeholder_id": "sh_founder_001",
      "share_percentage": 50
    }
  }'

# Platform keeps: 50% (99,500 VND)
# Founder receives: 50% (99,500 VND)
```

### User Spends Credits on AI Agent

```bash
# Debit credits for content generation (5 credits)
curl -X POST https://agencyos.network/v1/ledger/transfer \
  -H "Authorization: Bearer $RAAS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "from_code": "ACCT-CREDIT-001",
    "to_code": "ACCT-USAGE-001",
    "amount": 5,
    "currency": "CREDITS",
    "description": "Content generation (7 days)"
  }'

# User balance: 60 → 55 credits
```

---

## Balance Check Example

```bash
# Check all account balances for a tenant
curl -X GET "https://agencyos.network/v1/ledger/balance" \
  -H "Authorization: Bearer $RAAS_API_KEY"

# Response:
{
  "accounts": [
    {
      "code": "ACCT-CREDIT-001",
      "currency": "CREDITS",
      "balance": {
        "current": 55,
        "available": 55,
        "pending": 0,
        "reserved": 0
      }
    },
    {
      "code": "ACCT-USER-001",
      "currency": "VND",
      "balance": {
        "current": 101500,
        "available": 101500,
        "pending": 0,
        "reserved": 0
      }
    }
  ]
}
```

---

## Transaction History Query

```bash
# Last 20 transactions for credit account
curl -X GET "https://agencyos.network/v1/ledger/history?account_code=ACCT-CREDIT-001&limit=20" \
  -H "Authorization: Bearer $RAAS_API_KEY"

# Filter by type (topup only)
curl -X GET "https://agencyos.network/v1/ledger/history?type=topup" \
  -H "Authorization: Bearer $RAAS_API_KEY"
```

---

## Related Endpoints

- [GET /v1/billing/credits](./billing.md) — Check credit balance
- [POST /v1/payment/webhook/momo](./payment.md) — MoMo payment confirmation
- [POST /v1/payment/webhook/vnpay](./payment.md) — VNPAY payment confirmation
- [GET /v1/revenue/distribution](./revenue.md) — 6-way revenue split

---

## Next Steps

- [Equity API](./equity.md) — Equity entities, grants, cap tables
- [Revenue API](./revenue.md) — 6-way revenue split distribution
- [Funding API](./funding.md) — Quadratic funding rounds
