# RaaS Transaction Guide

**Version:** 1.0.0 | **Department:** Engineering + Finance | **Last Updated:** 2026-03-19

Hướng dẫn nghiệp vụ giao dịch cho nền tảng RaaS (Revenue-as-a-Service) với hệ thống double-entry accounting và equity management.

---

## Mục lục

1. [Tổng quan kiến trúc](#tổng-quan-kiến-trúc)
2. [Transaction Schema Examples](#transaction-schema-examples)
3. [Equity Restructuring](#equity-restructuring)
4. [Integration Patterns](#integration-patterns)
5. [Troubleshooting](#troubleshooting)

---

## Tổng quan kiến trúc

### Dòng tiền RaaS

```
Khách hàng → Payment (MoMo/VNPAY/Polar) → Ledger Topup → Account Balance
                                               ↓
                                    Revenue Distribution
                                               ↓
                              Platform | Expert | Community
```

### Hệ thống sổ kép (Double-Entry)

Mỗi giao dịch tạo **journal entry** với **transaction lines**:

| Thành phần | Mô tả |
|-----------|-------|
| `journal_entries` | Sổ nhật ký chung, mô tả giao dịch |
| `transaction_lines` | Dòng nghiệp vụ (debit/credit) |
| `ledger_accounts` | Tài khoản với balance = SUM(lines) |

**Công thức:** `balance = Σ(amount × direction)` với `direction ∈ {-1, 1}`

---

## Transaction Schema Examples

### 1. POST /v1/ledger/transfer

Chuyển khoản giữa hai tài khoản nội bộ.

#### Request Schema

```json
{
  "from_code": "revenue",
  "to_code": "expenses:expert_share",
  "amount": 150000,
  "description": "Expert share payment Q1/2026",
  "entry_type": "distribution",
  "idempotency_key": "dist_2026q1_expert_001"
}
```

#### Validation Rules (Zod)

```typescript
const transferSchema = z.object({
  from_code: z.string().min(1).max(100),      // Mã tài khoản nguồn
  to_code: z.string().min(1).max(100),        // Mã tài khoản đích
  amount: z.number()
    .positive('amount must be positive')
    .max(1_000_000_000, 'amount too large'),  // Giới hạn 1 tỷ VND
  description: z.string().max(500).optional(), // Mô tả ≤500 ký tự
  entry_type: z.string().max(50).optional(),  // Loại nghiệp vụ
  idempotency_key: z.string().max(100).optional(), // Chống trùng
})
```

#### Response (201 Created)

```json
{
  "journal_entry_id": "je_abc123xyz",
  "from": "revenue",
  "to": "expenses:expert_share",
  "amount": 150000
}
```

#### Journal Entry Structure

```sql
-- Journal Entry
INSERT INTO journal_entries (id, tenant_id, description, entry_type, idempotency_key)
VALUES ('je_abc123xyz', 'tn_001', 'Expert share payment Q1/2026', 'distribution', 'dist_2026q1_expert_001');

-- Transaction Lines (2 dòng)
INSERT INTO transaction_lines (id, journal_entry_id, account_id, amount, direction)
VALUES
  ('line1', 'je_abc123xyz', 'acct_revenue', 150000, -1),  -- Debit: giảm revenue
  ('line2', 'je_abc123xyz', 'acct_expenses', 150000, 1);  -- Credit: tăng expenses

-- Update Balances (atomic)
UPDATE ledger_accounts SET balance = balance - 150000 WHERE id = 'acct_revenue';
UPDATE ledger_accounts SET balance = balance + 150000 WHERE id = 'acct_expenses';
```

#### Idempotency Check

```typescript
// Kiểm tra trước khi xử lý
const existing = await db.prepare(
  'SELECT id FROM journal_entries WHERE idempotency_key = ?'
).bind(body.idempotency_key).first();

if (existing) {
  return c.json({
    journal_entry_id: existing.id,
    status: 'already_processed'
  });
}
```

---

### 2. POST /v1/ledger/topup

Nạp tiền vào tài khoản từ platform treasury.

#### Request Schema

```json
{
  "account_code": "revenue",
  "amount": 1000000,
  "description": "MoMo payment topup - Order #MOM_123456"
}
```

#### Validation Rules (Zod)

```typescript
const topupSchema = z.object({
  account_code: z.string().min(1).max(100),  // Mã tài khoản nhận
  amount: z.number()
    .positive('amount must be positive')
    .max(1_000_000_000, 'amount too large'),
  description: z.string().max(500).optional(),
})
```

#### Response (201 Created)

```json
{
  "journal_entry_id": "je_topup789",
  "account": "revenue",
  "credited": 1000000
}
```

#### Journal Entry Structure

```sql
-- Tạo tài khoản platform:treasury nếu chưa tồn tại
INSERT INTO ledger_accounts (id, tenant_id, code, account_type)
VALUES ('uuid', 'tn_001', 'platform:treasury', 'equity');

-- Journal Entry
INSERT INTO journal_entries (id, tenant_id, description, entry_type)
VALUES ('je_topup789', 'tn_001', 'MoMo payment topup - Order #MOM_123456', 'topup');

-- Transaction Lines
INSERT INTO transaction_lines (id, journal_entry_id, account_id, amount, direction)
VALUES
  ('line1', 'je_topup789', 'acct_treasury', 1000000, -1),  -- Debit: giảm treasury
  ('line2', 'je_topup789', 'acct_revenue', 1000000, 1);    -- Credit: tăng revenue

-- Update Balance
UPDATE ledger_accounts SET balance = balance + 1000000 WHERE code = 'revenue';
```

---

### 3. GET /v1/ledger/balance

Xem số dư tài khoản.

#### Query Parameters

| Param | Type | Description |
|-------|------|-------------|
| `code` | string (optional) | Filter by account code |

#### Examples

```bash
# Tất cả tài khoản
GET /v1/ledger/balance

# Filter theo code
GET /v1/ledger/balance?code=revenue
```

#### Response

```json
{
  "accounts": [
    {
      "id": "acct_001",
      "tenant_id": "tn_001",
      "code": "revenue",
      "account_type": "asset",
      "balance": 2500000,
      "created_at": "2026-01-15T10:30:00Z"
    },
    {
      "id": "acct_002",
      "tenant_id": "tn_001",
      "code": "expenses:expert_share",
      "account_type": "liability",
      "balance": 450000,
      "created_at": "2026-01-15T10:35:00Z"
    }
  ]
}
```

---

### 4. GET /v1/ledger/history

Xem lịch sử giao dịch.

#### Query Parameters

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `limit` | number | 30 | Số bản ghi (tối đa 100) |

#### Response

```json
{
  "entries": [
    {
      "id": "je_abc123",
      "tenant_id": "tn_001",
      "description": "Expert share payment",
      "entry_type": "distribution",
      "posted_at": "2026-03-19T14:30:00Z",
      "lines": "acct_revenue:150000:-1,acct_expenses:150000:1"
    }
  ]
}
```

**Lines format:** `account_id:amount:direction` (phân cách bằng dấu phẩy)

---

## Equity Restructuring

### 1. SAFE Note Conversion

Chuyển đổi SAFE note sang equity (Common shares).

#### Công thức tính shares

```typescript
// Bước 1: Tính effective price với discount
const effectivePrice = price_per_share * (1 - discount_rate);

// Bước 2: Tính shares từ principal
let shares = Math.floor(principal_amount / effectivePrice);

// Bước 3: So sánh với valuation cap (lấy lợi hơn cho investor)
if (valuation_cap) {
  const capShares = Math.floor(
    principal_amount / (valuation_cap / total_authorized_shares)
  );
  shares = Math.max(shares, capShares); // Investor gets better deal
}
```

#### Ví dụ thực tế

**Input:**
- Principal: $100,000
- Price per share: $1.00
- Discount rate: 20% (0.20)
- Valuation cap: $5,000,000
- Total authorized shares: 10,000,000

**Tính toán:**

```
Effective Price = $1.00 × (1 - 0.20) = $0.80
Discount Shares = $100,000 / $0.80 = 125,000 shares

Cap Price = $5,000,000 / 10,000,000 = $0.50
Cap Shares = $100,000 / $0.50 = 200,000 shares

Final Shares = max(125,000, 200,000) = 200,000 shares
```

#### Request Schema (POST /v1/equity/safe/:id/convert)

```json
{
  "price_per_share": 1.00,
  "share_class_id": "sc_common_xyz"
}
```

#### Response

```json
{
  "grant_id": "grant_mno345",
  "shares_converted": 200000,
  "effective_price": 0.5000
}
```

#### Database Operations (Batch)

```sql
-- Tạo equity grant
INSERT INTO equity_grants (
  id, entity_id, stakeholder_id, share_class_id,
  grant_type, shares, price_per_share
) VALUES (
  'grant_mno345', 'ent_abc', 'stk_inv123', 'sc_common_xyz',
  'conversion', 200000, 0.50
);

-- Cập nhật SAFE status
UPDATE safe_notes
SET status = 'converted',
    conversion_date = datetime('now'),
    converted_shares = 200000
WHERE id = 'safe_001';
```

---

### 2. Equity Grant Issuance

Phát hành equity grant cho stakeholder với vesting schedule.

#### Request Schema (POST /v1/equity/grants)

```json
{
  "entity_id": "ent_abc123",
  "stakeholder_id": "stk_def456",
  "share_class_id": "sc_xyz789",
  "shares": 10000,
  "price_per_share": 0.001,
  "grant_type": "grant",
  "vesting_months": 48,
  "cliff_months": 12
}
```

#### Validation Rules (Zod)

```typescript
const createGrantSchema = z.object({
  entity_id: z.string().uuid('entity_id must be a valid UUID'),
  stakeholder_id: z.string().uuid('stakeholder_id must be a valid UUID'),
  share_class_id: z.string().uuid('share_class_id must be a valid UUID'),
  shares: z.number().int().positive('shares must be positive'),
  price_per_share: z.number()
    .nonnegative('price_per_share must be non-negative')
    .optional(),
  grant_type: z.string().optional(), // 'grant' | 'exercise' | 'conversion'
  vesting_months: z.number()
    .int()
    .nonnegative('vesting_months must be non-negative')
    .optional(),
  cliff_months: z.number()
    .int()
    .nonnegative('cliff_months must be non-negative')
    .optional(),
})
```

#### Vesting Calculation

```typescript
const now = new Date();
const start = new Date(vesting_start_date);
const monthsElapsed = Math.max(
  0,
  (now.getTime() - start.getTime()) / (30.44 * 24 * 60 * 60 * 1000)
);

// Trước cliff: 0% vested
if (monthsElapsed < cliff_months) {
  vested_shares = 0;
  vested_pct = 0;
} else {
  // Sau cliff: vest theo tỷ lệ thời gian
  const vestedPct = Math.min(100, (monthsElapsed / vesting_months) * 100);
  vested_shares = Math.floor(shares * vestedPct / 100);
  vested_pct = Math.round(vestedPct);
}
```

#### Ví dụ vesting schedule

**Grant:** 10,000 shares, 48 months, 12 months cliff

| Thời điểm | Months Elapsed | Vested % | Vested Shares |
|-----------|---------------|----------|---------------|
| Month 0 | 0 | 0% | 0 |
| Month 6 | 6 | 0% (trước cliff) | 0 |
| Month 12 | 12 | 25% | 2,500 |
| Month 24 | 24 | 50% | 5,000 |
| Month 36 | 36 | 75% | 7,500 |
| Month 48 | 48 | 100% | 10,000 |

---

### 3. Cap Table Computation

Bảng cap table được tính toán từ equity_grants.

#### SQL Query

```sql
-- Aggregate grants per stakeholder
SELECT
  g.stakeholder_id,
  s.display_name,
  s.role,
  sc.name as share_class,
  SUM(CASE
    WHEN g.grant_type IN ('grant','exercise','conversion')
    THEN g.shares
    ELSE 0
  END) as total_granted,
  SUM(CASE
    WHEN g.grant_type IN ('cancellation')
    THEN g.shares
    ELSE 0
  END) as total_cancelled
FROM equity_grants g
JOIN stakeholders s ON s.id = g.stakeholder_id
JOIN share_classes sc ON sc.id = g.share_class_id
WHERE g.entity_id = ?
GROUP BY g.stakeholder_id, sc.name
ORDER BY total_granted DESC;
```

#### Response Structure (GET /v1/equity/cap-table/:entityId)

```json
{
  "entity": {
    "name": "Acme Corporation",
    "total_authorized": 10000000
  },
  "total_outstanding": 2500000,
  "dilution_pct": "25.00",
  "holders": [
    {
      "stakeholder_id": "stk_def456",
      "display_name": "Alice Nguyen",
      "role": "expert",
      "share_class": "Common",
      "total_granted": 10000,
      "total_cancelled": 0
    }
  ],
  "vesting_schedule": [
    {
      "grant_id": "grant_ghi789",
      "shares": 10000,
      "vested_shares": 2500,
      "vested_pct": 25,
      "vesting_start_date": "2025-03-19",
      "vesting_months": 48,
      "cliff_months": 12
    }
  ],
  "safe_notes": [
    {
      "id": "safe_jkl012",
      "investor_stakeholder_id": "stk_inv123",
      "display_name": "Bob Investor",
      "principal_amount": 100000,
      "valuation_cap": 5000000,
      "discount_rate": 0.2,
      "status": "outstanding"
    }
  ]
}
```

#### Dilution Calculation

```typescript
const dilution_pct = (total_outstanding / total_authorized_shares) * 100;
// Ví dụ: 2,500,000 / 10,000,000 = 25.00%
```

---

### 4. Entity Creation with Auto Share Class

Tạo portfolio entity tự động sinh Common share class.

#### Request Schema (POST /v1/equity/entities)

```json
{
  "name": "Acme Corporation",
  "entity_type": "portfolio_company",
  "total_shares": 10000000,
  "jurisdiction": "VN"
}
```

#### Database Operations

```sql
-- Step 1: Tạo entity
INSERT INTO equity_entities (
  id, tenant_id, name, entity_type, total_authorized_shares, jurisdiction
) VALUES (
  'ent_abc123', 'tn_001', 'Acme Corporation',
  'portfolio_company', 10000000, 'VN'
);

-- Step 2: Auto-create Common share class
INSERT INTO share_classes (
  id, entity_id, name, class_type
) VALUES (
  'sc_xyz789', 'ent_abc123', 'Common', 'common'
);
```

#### Response

```json
{
  "id": "ent_abc123",
  "share_class_id": "sc_xyz789"
}
```

---

## Integration Patterns

### 1. Payment → Ledger Topup Flow

```
MoMo/VNPAY IPN → Verify signature → Check replay attack
                                            ↓
                              INSERT INTO payment_logs (unique_tx_id)
                                            ↓ (if new)
                              POST /v1/ledger/topup
                                            ↓
                              Journal Entry + Balance Update
```

#### Code Example (payment-vn.ts)

```typescript
// Step 1: Verify HMAC signature
const expectedSig = crypto.createHmac(
  'sha256',
  process.env.MOMO_SECRET_KEY
).update(rawBody).digest('hex');

if (signature !== expectedSig) {
  return c.json(createError('UNAUTHORIZED', 'Invalid signature'), 401);
}

// Step 2: Check replay attack
const existing = await db.prepare(
  'SELECT id FROM payment_logs WHERE transaction_id = ?'
).bind(partnerCode + orderId).first();

if (existing) {
  return c.json({ status: 'already_processed' }); // Idempotent
}

// Step 3: Log transaction (prevent replay)
await db.prepare(
  'INSERT INTO payment_logs (tenant_id, transaction_id, amount, status) VALUES (?, ?, ?, ?)'
).bind(tenantId, partnerCode + orderId, amount, 'pending').run();

// Step 4: Topup ledger
const topupId = crypto.randomUUID();
await db.batch([
  db.prepare('INSERT INTO journal_entries ...').bind(topupId, tenantId, ...),
  db.prepare('INSERT INTO transaction_lines ...'),
  db.prepare('UPDATE ledger_accounts SET balance = balance + ?').bind(amount, acctId),
]);

// Step 5: Update payment log status
await db.prepare(
  'UPDATE payment_logs SET status = ? WHERE transaction_id = ?'
).bind('completed', partnerCode + orderId).run();
```

---

### 2. Revenue Distribution Flow

```
Revenue Account (balance) → GET /v1/revenue/splits (config)
                                     ↓
                        Calculate splits (platform/expert/community)
                                     ↓
                        POST /v1/ledger/transfer (multiple)
                                     ↓
                        Revenue → Platform Share
                        Revenue → Expert Share
                        Revenue → Community Fund
```

#### Example Distribution

**Total Revenue:** 1,000,000 VND

**Split Configuration:**
- Platform: 20% → 200,000 VND
- Expert: 30% → 300,000 VND
- AI Compute: 15% → 150,000 VND
- Developer: 15% → 150,000 VND
- Community Fund: 10% → 100,000 VND
- Customer Reward: 10% → 100,000 VND

**API Calls:**

```bash
# Transfer 1: Revenue → Platform
POST /v1/ledger/transfer
{
  "from_code": "revenue",
  "to_code": "platform:share",
  "amount": 200000,
  "description": "Platform share 20%",
  "idempotency_key": "dist_2026q1_platform"
}

# Transfer 2: Revenue → Expert
POST /v1/ledger/transfer
{
  "from_code": "revenue",
  "to_code": "expert:share",
  "amount": 300000,
  "description": "Expert share 30%",
  "idempotency_key": "dist_2026q1_expert"
}

# ... (tương tự cho các phần còn lại)
```

---

### 3. SAFE Conversion → Equity → Vesting

```
Investor → POST /v1/equity/safe (issue SAFE)
              ↓
     SAFE Note (outstanding)
              ↓
     Trigger: priced round
              ↓
POST /v1/equity/safe/:id/convert
              ↓
     Equity Grant (conversion) + Vesting Schedule
              ↓
     Cap Table Updated (dilution recalculated)
```

#### Timeline Example

| Date | Event | Shares | Notes |
|------|-------|--------|-------|
| 2025-01-15 | Issue SAFE | - | $100k principal, $5M cap, 20% discount |
| 2025-06-01 | Priced round | - | Price per share: $1.00 |
| 2025-06-01 | Convert SAFE | 200,000 | Cap price: $0.50 (better than discount $0.80) |
| 2025-06-01 | Vesting starts | - | 48 months, 12 months cliff |
| 2026-06-01 | Cliff reached | 50,000 | 25% vested (after 12 months) |
| 2027-06-01 | 50% vested | 100,000 | After 24 months |
| 2029-06-01 | Fully vested | 200,000 | After 48 months |

---

## Troubleshooting

### Lỗi thường gặp

#### 1. "Insufficient balance" khi transfer

**Nguyên nhân:** Tài khoản nguồn không đủ số dư.

**Giải pháp:**
```bash
# Kiểm tra balance trước khi transfer
GET /v1/ledger/balance?code=revenue

# Nếu balance < amount → topup trước
POST /v1/ledger/topup
{
  "account_code": "revenue",
  "amount": <thiếu_hbao_nhiêu>
}
```

---

#### 2. "Duplicate idempotency_key"

**Nguyên nhân:** Giao dịch đã được xử lý trước đó.

**Giải pháp:**
```bash
# Kiểm tra journal entry tồn tại
SELECT * FROM journal_entries WHERE idempotency_key = '<key>';

# Nếu status = 'already_processed' → giao dịch đã thành công
# Nếu cần retry → dùng idempotency_key mới
```

---

#### 3. SAFE conversion cho shares âm

**Nguyên nhân:** Price per share = 0 hoặc discount_rate > 1.

**Validation:**
```typescript
// Zod schema đảm bảo
price_per_share: z.number().positive(),
discount_rate: z.number().min(0).max(1),
```

**Kiểm tra trước khi convert:**
```bash
# Xem SAFE details
SELECT * FROM safe_notes WHERE id = '<safe_id>';

# Đảm bảo:
# - principal_amount > 0
# - discount_rate ∈ [0, 1]
# - valuation_cap > 0 (nếu có)
```

---

#### 4. Vesting calculation sai

**Nguyên nhân:** Múi giờ hoặc vesting_start_date không đúng.

**Giải pháp:**
```sql
-- Kiểm tra vesting_start_date
SELECT id, vesting_start_date, vesting_months, cliff_months
FROM equity_grants WHERE id = '<grant_id>';

-- Tính monthsElapsed thủ công
SELECT
  julianday('now') - julianday(vesting_start_date) as days_elapsed,
  (julianday('now') - julianday(vesting_start_date)) / 30.44 as months_elapsed
FROM equity_grants WHERE id = '<grant_id>';
```

---

### Debug Queries

```sql
-- Xem tất cả journal entries của tenant
SELECT * FROM journal_entries
WHERE tenant_id = 'tn_001'
ORDER BY posted_at DESC
LIMIT 50;

-- Xem transaction lines của journal entry
SELECT tl.*, la.code as account_code
FROM transaction_lines tl
JOIN ledger_accounts la ON tl.account_id = la.id
WHERE tl.journal_entry_id = 'je_abc123';

-- Xem balance tất cả accounts
SELECT code, account_type, balance
FROM ledger_accounts
WHERE tenant_id = 'tn_001'
ORDER BY code;

-- Xem equity grants chưa vest hết
SELECT
  g.id, g.shares, g.vested_shares,
  (g.shares - g.vested_shares) as unvested,
  g.vesting_start_date, g.vesting_months
FROM equity_grants g
WHERE g.entity_id = 'ent_abc123'
  AND g.vested_shares < g.shares;

-- Xem SAFE notes chưa convert
SELECT * FROM safe_notes
WHERE entity_id = 'ent_abc123'
  AND status = 'outstanding';
```

---

## Phụ lục

### A. Account Code Conventions

| Pattern | Description | Example |
|---------|-------------|---------|
| `revenue` | Doanh thu chính | `revenue` |
| `expenses:*` | Chi phí (có thể phân cấp) | `expenses:expert_share`, `expenses:ai_compute` |
| `platform:*` | Tài khoản platform | `platform:share`, `platform:treasury` |
| `community:*` | Quỹ cộng đồng | `community:fund`, `community:rewards` |
| `equity:*` | Equity accounts | `equity:common`, `equity:preferred` |
| `liability:*` | Nợ phải trả | `liability:unearned_revenue` |

### B. Entry Type Values

| Value | Description |
|-------|-------------|
| `transfer` | Chuyển khoản nội bộ |
| `topup` | Nạp tiền từ bên ngoài |
| `distribution` | Phân chia doanh thu |
| `payment` | Thanh toán chi phí |
| `conversion` | Chuyển đổi SAFE/equity |
| `grant` | Phát hành equity grant |
| `cancellation` | Hủy equity |

### C. Error Codes

| Code | HTTP | Description |
|------|------|-------------|
| `INSUFFICIENT_CREDITS` | 402 | Số dư không đủ |
| `DUPLICATE_ENTRY` | 409 | Idempotency key trùng |
| `NOT_FOUND` | 404 | Account/Entity/SAFE không tồn tại |
| `VALIDATION_ERROR` | 400 | Zod validation failed |
| `CONFLICT` | 409 | Chỉ có thể cancel pending missions |

---

*Tài liệu nội bộ — Chỉ dành cho team Engineering + Finance*
