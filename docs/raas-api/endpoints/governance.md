# Governance API — Quadratic Voting & Proposals

> **Purpose**: Hệ thống quản trị phi tập trung với quadratic voting và đề xuất đa stakeholder.

---

## Endpoints Overview

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/v1/governance/stakeholders` | ✅ | Create stakeholder with role |
| GET | `/v1/governance/stakeholders` | ✅ | List stakeholders |
| POST | `/v1/governance/proposals` | ✅ | Create proposal for voting |
| GET | `/v1/governance/proposals` | ✅ | List proposals with filters |
| POST | `/v1/governance/vote` | ✅ | Cast quadratic vote |
| POST | `/v1/governance/reputation` | ✅ | Calculate Ngũ Sự reputation |

---

## POST /v1/governance/stakeholders — Create Stakeholder

### Request

```bash
curl -X POST https://agencyos.network/v1/governance/stakeholders \
  -H "Authorization: Bearer $RAAS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Nguyen Van A",
    "role": "founder",
    "governance_level": 5,
    "metadata": {
      "email": "founder@agencyos.network",
      "contribution": "Initial concept and architecture"
    }
  }'
```

### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | ✅ | Stakeholder display name |
| `role` | string | ✅ | Stakeholder role (see below) |
| `governance_level` | integer | ❌ | Voting power level (1-10, default: 1) |
| `metadata` | object | ❌ | Additional stakeholder data |

### Stakeholder Roles

| Role | Governance Weight | Description |
|------|-------------------|-------------|
| `owner` | 10 | Legal owner, ultimate authority |
| `admin` | 8 | Platform administrator |
| `operator` | 6 | Day-to-day operations manager |
| `vc_partner` | 7 | Venture capital partner |
| `founder` | 9 | Company founder |
| `expert` | 5 | Domain expert advisor |
| `developer` | 4 | Core contributor |
| `customer` | 3 | Paying customer |
| `community` | 2 | Community member |

### Response (201 Created)

```json
{
  "id": "stakeholder_abc123",
  "name": "Nguyen Van A",
  "role": "founder",
  "governance_level": 5,
  "reputation_score": 0,
  "voting_power": 5,
  "metadata": {
    "email": "founder@agencyos.network",
    "contribution": "Initial concept and architecture"
  },
  "created_at": "2026-03-19T10:00:00Z",
  "updated_at": "2026-03-19T10:00:00Z"
}
```

### Stakeholder Object

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique stakeholder ID |
| `name` | string | Display name |
| `role` | string | Stakeholder role |
| `governance_level` | integer | Base voting power (1-10) |
| `reputation_score` | float | Ngũ Sự reputation score (0-100) |
| `voting_power` | integer | Current voting power |
| `metadata` | object | Custom data |
| `created_at` | string | ISO 8601 timestamp |
| `updated_at` | string | ISO 8601 timestamp |

### Error Responses

**400 Invalid Role:**
```json
{
  "error": "VALIDATION_ERROR",
  "message": "Invalid role. Must be one of: owner, admin, operator, vc_partner, founder, expert, developer, customer, community"
}
```

**400 Invalid Governance Level:**
```json
{
  "error": "VALIDATION_ERROR",
  "message": "governance_level must be between 1 and 10"
}
```

---

## GET /v1/governance/stakeholders — List Stakeholders

### Request

```bash
curl -X GET "https://agencyos.network/v1/governance/stakeholders?role=founder&limit=50" \
  -H "Authorization: Bearer $RAAS_API_KEY"
```

### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `role` | string | ❌ | Filter by stakeholder role |
| `limit` | integer | ❌ | Max results (default: 50, max: 100) |
| `offset` | integer | ❌ | Pagination offset (default: 0) |
| `min_governance_level` | integer | ❌ | Minimum governance level filter |

### Response (200 OK)

```json
{
  "stakeholders": [
    {
      "id": "stakeholder_abc123",
      "name": "Nguyen Van A",
      "role": "founder",
      "governance_level": 5,
      "reputation_score": 78.5,
      "voting_power": 5,
      "metadata": {
        "email": "founder@agencyos.network"
      },
      "created_at": "2026-03-01T08:00:00Z",
      "updated_at": "2026-03-19T10:00:00Z"
    },
    {
      "id": "stakeholder_def456",
      "name": "Tran Thi B",
      "role": "developer",
      "governance_level": 4,
      "reputation_score": 92.3,
      "voting_power": 4,
      "metadata": {
        "email": "dev@agencyos.network",
        "github": "@tranb"
      },
      "created_at": "2026-03-05T12:00:00Z",
      "updated_at": "2026-03-18T14:30:00Z"
    }
  ],
  "total": 47,
  "limit": 50,
  "offset": 0
}
```

---

## POST /v1/governance/proposals — Create Proposal

### Request

```bash
curl -X POST https://agencyos.network/v1/governance/proposals \
  -H "Authorization: Bearer $RAAS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Add LinkedIn content generation agent",
    "description": "Expand content generation capabilities to include LinkedIn professional posts with industry-specific formatting.",
    "type": "feature",
    "requested_funding": 50000000,
    "metadata": {
      "priority": "high",
      "estimated_credits": 500,
      "timeline": "2 weeks"
    }
  }'
```

### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `title` | string | ✅ | Proposal title |
| `description` | string | ✅ | Detailed proposal description |
| `type` | string | ✅ | Proposal type (see below) |
| `requested_funding` | integer | ❌ | Funding requested in VND |
| `metadata` | object | ❌ | Additional proposal data |

### Proposal Types

| Type | Quorum Required | Approval Threshold | Description |
|------|-----------------|-------------------|-------------|
| `feature` | 20% | 60% | New feature request |
| `strategic` | 40% | 70% | Strategic direction change |
| `constitutional` | 60% | 80% | Governance rule change |
| `treasury` | 30% | 65% | Fund allocation |
| `equity` | 50% | 75% | Equity distribution |

### Response (201 Created)

```json
{
  "id": "proposal_abc123",
  "title": "Add LinkedIn content generation agent",
  "description": "Expand content generation capabilities to include LinkedIn professional posts with industry-specific formatting.",
  "type": "feature",
  "status": "draft",
  "requested_funding": 50000000,
  "metadata": {
    "priority": "high",
    "estimated_credits": 500,
    "timeline": "2 weeks"
  },
  "author_id": "stakeholder_abc123",
  "votes_for": 0,
  "votes_against": 0,
  "vote_credits_for": 0,
  "vote_credits_against": 0,
  "quorum_reached": false,
  "passed": false,
  "created_at": "2026-03-19T10:30:00Z",
  "updated_at": "2026-03-19T10:30:00Z",
  "voting_deadline": "2026-03-26T10:30:00Z"
}
```

### Proposal Object

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique proposal ID |
| `title` | string | Proposal title |
| `description` | string | Detailed description |
| `type` | string | Proposal type |
| `status` | string | `draft`, `active`, `passed`, `rejected`, `executed` |
| `requested_funding` | integer | Funding requested in VND |
| `metadata` | object | Custom data |
| `author_id` | string | Stakeholder who created proposal |
| `votes_for` | integer | Number of votes in favor |
| `votes_against` | integer | Number of votes against |
| `vote_credits_for` | integer | Total credit weight in favor |
| `vote_credits_against` | integer | Total credit weight against |
| `quorum_reached` | boolean | Whether quorum threshold met |
| `passed` | boolean | Whether proposal passed |
| `created_at` | string | ISO 8601 timestamp |
| `updated_at` | string | ISO 8601 timestamp |
| `voting_deadline` | string | Voting deadline (7 days from creation) |

### Proposal Lifecycle

```
┌─────────┐     ┌─────────┐     ┌─────────┐     ┌──────────┐     ┌──────────┐
│  draft  │ →   │ active  │ →   │ voting  │ →   │ passed   │ →   │ executed │
└─────────┘     └─────────┘     └─────────┘     └──────────┘     └──────────┘
     ↓               ↓               ↓               ↓                ↓
  Created        Published      Voting          Quorum +        Implementation
  by author      to all         period          threshold       complete
                 stakeholders   (7 days)        met
```

### Error Responses

**400 Invalid Type:**
```json
{
  "error": "VALIDATION_ERROR",
  "message": "Invalid proposal type. Must be one of: feature, strategic, constitutional, treasury, equity"
}
```

---

## GET /v1/governance/proposals — List Proposals

### Request

```bash
curl -X GET "https://agencyos.network/v1/governance/proposals?status=active&type=feature" \
  -H "Authorization: Bearer $RAAS_API_KEY"
```

### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `status` | string | ❌ | Filter by status: `draft`, `active`, `passed`, `rejected`, `executed` |
| `type` | string | ❌ | Filter by proposal type |
| `limit` | integer | ❌ | Max results (default: 50, max: 100) |
| `offset` | integer | ❌ | Pagination offset (default: 0) |

### Response (200 OK)

```json
{
  "proposals": [
    {
      "id": "proposal_abc123",
      "title": "Add LinkedIn content generation agent",
      "description": "Expand content generation capabilities...",
      "type": "feature",
      "status": "active",
      "requested_funding": 50000000,
      "author_id": "stakeholder_abc123",
      "votes_for": 12,
      "votes_against": 3,
      "vote_credits_for": 450,
      "vote_credits_against": 85,
      "quorum_reached": true,
      "passed": false,
      "voting_deadline": "2026-03-26T10:30:00Z",
      "created_at": "2026-03-19T10:30:00Z",
      "updated_at": "2026-03-20T14:00:00Z"
    },
    {
      "id": "proposal_def456",
      "title": "Q2 Marketing Budget Allocation",
      "description": "Allocate 500M VND for Q2 marketing campaigns...",
      "type": "treasury",
      "status": "passed",
      "requested_funding": 500000000,
      "author_id": "stakeholder_def456",
      "votes_for": 28,
      "votes_against": 5,
      "vote_credits_for": 1250,
      "vote_credits_against": 120,
      "quorum_reached": true,
      "passed": true,
      "voting_deadline": "2026-03-15T10:00:00Z",
      "executed_at": "2026-03-16T09:00:00Z",
      "created_at": "2026-03-08T10:00:00Z",
      "updated_at": "2026-03-16T09:00:00Z"
    }
  ],
  "total": 23,
  "limit": 50,
  "offset": 0
}
```

---

## POST /v1/governance/vote — Cast Quadratic Vote

### Request

```bash
curl -X POST https://agencyos.network/v1/governance/vote \
  -H "Authorization: Bearer $RAAS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "proposal_id": "proposal_abc123",
    "support": true,
    "credits": 100
  }'
```

### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `proposal_id` | string | ✅ | Proposal to vote on |
| `support` | boolean | ✅ | `true` for support, `false` for against |
| `credits` | integer | ✅ | Credits to spend (determines vote power) |

### Quadratic Voting Formula

```
votes = √credits
cost = votes² = credits

Example:
- Spend 100 credits → 10 votes (√100 = 10)
- Spend 400 credits → 20 votes (√400 = 20)
- Spend 900 credits → 30 votes (√900 = 30)

Marginal cost increases quadratically:
- 1st vote: 1 credit
- 10th vote: 19 credits (10² - 9² = 100 - 81)
- 20th vote: 39 credits (20² - 19² = 400 - 361)
```

### Quadratic Voting Benefits

| Problem | Quadratic Solution |
|---------|-------------------|
| Wealth dominance | Diminishing returns on vote buying |
| Minority suppression | Intense preferences can be expressed |
| Vote buying | Exponentially expensive to buy many votes |
| Plurality tyranny | Compromise candidates benefit |

### Response (200 OK)

```json
{
  "vote_id": "vote_abc123",
  "proposal_id": "proposal_abc123",
  "stakeholder_id": "stakeholder_abc123",
  "support": true,
  "credits_spent": 100,
  "votes_cast": 10,
  "proposal_status": "active",
  "updated_totals": {
    "votes_for": 13,
    "votes_against": 3,
    "vote_credits_for": 550,
    "vote_credits_against": 85,
    "quorum_reached": true,
    "quorum_percentage": 0.68
  },
  "created_at": "2026-03-19T11:00:00Z"
}
```

### Vote Object

| Field | Type | Description |
|-------|------|-------------|
| `vote_id` | string | Unique vote ID |
| `proposal_id` | string | Proposal voted on |
| `stakeholder_id` | string | Voter stakeholder ID |
| `support` | boolean | Vote direction |
| `credits_spent` | integer | Credits consumed |
| `votes_cast` | float | Vote power (√credits) |
| `proposal_status` | string | Current proposal status |
| `updated_totals` | object | Updated vote totals |
| `created_at` | string | ISO 8601 timestamp |

### Error Responses

**400 Invalid Proposal:**
```json
{
  "error": "VALIDATION_ERROR",
  "message": "Proposal not found or voting closed"
}
```

**400 Insufficient Credits:**
```json
{
  "error": "INSUFFICIENT_CREDITS",
  "message": "Stakeholder has 50 credits, attempted to spend 100"
}
```

**400 Already Voted:**
```json
{
  "error": "CONFLICT",
  "message": "Stakeholder has already voted on this proposal"
}
```

---

## POST /v1/governance/reputation — Calculate Ngũ Sự Reputation

### Request

```bash
curl -X POST https://agencyos.network/v1/governance/reputation \
  -H "Authorization: Bearer $RAAS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "stakeholder_id": "stakeholder_abc123"
  }'
```

### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `stakeholder_id` | string | ✅ | Stakeholder to calculate reputation for |

### Ngũ Sự Scoring System (五事 - Five Affairs)

| Element | Weight | Metrics |
|---------|--------|---------|
| **Đạo (道)** | 30% | Alignment with mission, values adherence |
| **Thiên (天)** | 25% | Market timing, trend awareness |
| **Địa (地)** | 20% | Market position, competitive landscape |
| **Tướng (將)** | 15% | Leadership quality, decision-making |
| **Pháp (法)** | 10% | Process discipline, execution quality |

### Scoring Calculation

```typescript
function calculateReputation(stakeholder: Stakeholder): ReputationScore {
  const dao = calculateMissionAlignment(stakeholder);      // 0-100
  const thien = calculateMarketTiming(stakeholder);        // 0-100
  const diai = calculateMarketPosition(stakeholder);       // 0-100
  const tuong = calculateLeadershipQuality(stakeholder);   // 0-100
  const phap = calculateProcessDiscipline(stakeholder);    // 0-100

  const weightedScore =
    (dao * 0.30) +
    (thien * 0.25) +
    (diai * 0.20) +
    (tuong * 0.15) +
    (phap * 0.10);

  return {
    total: weightedScore,
    breakdown: { dao, thien, diai, tuong, phap }
  };
}
```

### Response (200 OK)

```json
{
  "stakeholder_id": "stakeholder_abc123",
  "reputation_score": 78.5,
  "breakdown": {
    "dao": 85,
    "thien": 72,
    "diai": 80,
    "tuong": 75,
    "phap": 78
  },
  "percentile": 0.68,
  "rank": 12,
  "total_stakeholders": 47,
  "last_calculated": "2026-03-19T11:30:00Z"
}
```

### Reputation Score Object

| Field | Type | Description |
|-------|------|-------------|
| `stakeholder_id` | string | Stakeholder ID |
| `reputation_score` | float | Total weighted score (0-100) |
| `breakdown` | object | Ngũ Sự element scores |
| `percentile` | float | Percentile rank (0-1) |
| `rank` | integer | Overall rank among stakeholders |
| `total_stakeholders` | integer | Total stakeholder count |
| `last_calculated` | string | ISO 8601 timestamp |

### Reputation Impact

| Score Range | Tier | Benefits |
|-------------|------|----------|
| 90-100 | Sage | 2x voting power, proposal priority |
| 80-89 | Expert | 1.5x voting power, early access |
| 70-79 | Trusted | Standard voting, full access |
| 60-69 | Member | Reduced voting power |
| <60 | Novice | Limited proposal rights |

---

## Governance Data Flow

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Stakeholder    │ →   │  Proposal       │ →   │  Voting Period  │
│  Registration   │     │  Creation       │     │  (7 days)       │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                       │
                                                       ↓
                                            ┌─────────────────┐
                                            │  Quadratic      │
                                            │  Vote Casting   │
                                            └─────────────────┘
                                                       │
                                        ┌──────────────┴──────────────┐
                                        ↓                              ↓
                               ┌─────────────────┐          ┌─────────────────┐
                               │  Quorum +       │          │  Reputation     │
                               │  Threshold Met? │          │  Recalculation  │
                               └─────────────────┘          └─────────────────┘
                                        │
                              ┌─────────┴─────────┐
                              ↓                   ↓
                     ┌─────────────────┐ ┌─────────────────┐
                     │  PASSED         │ │  REJECTED       │
                     │  Execute        │ │  Archive        │
                     └─────────────────┘ └─────────────────┘
```

---

## Use Cases

### Feature Proposal with Funding

```json
{
  "title": "Build TikTok content agent",
  "description": "Create AI agent for short-form video script generation",
  "type": "feature",
  "requested_funding": 30000000,
  "metadata": {
    "priority": "medium",
    "estimated_timeline": "3 weeks",
    "required_agents": ["content-writer", "recipe-crawler"]
  }
}

// Voting outcome example:
// - 45 stakeholders vote
// - 38 support (84%), 7 against (16%)
// - Total credits for: 2,450
// - Total credits against: 180
// - Quorum: 68% (required: 20% for feature)
// - Result: PASSED
```

### Constitutional Amendment

```json
{
  "title": "Change quorum requirement for treasury proposals",
  "description": "Increase quorum from 30% to 40% for treasury proposals to ensure broader consensus on fund allocation",
  "type": "constitutional",
  "metadata": {
    "current_rule": "30% quorum for treasury",
    "proposed_rule": "40% quorum for treasury",
    "rationale": "Higher stakes require broader participation"
  }
}

// Requires:
// - 60% quorum (vs 20% for feature)
// - 80% approval (vs 60% for feature)
```

### Treasury Allocation

```json
{
  "title": "Q2 2026 Marketing Budget",
  "description": "Allocate 1.5B VND for Q2 marketing: 600M digital ads, 400M content, 300M events, 200M partnerships",
  "type": "treasury",
  "requested_funding": 1500000000,
  "metadata": {
    "quarter": "Q2 2026",
    "breakdown": {
      "digital_ads": 600000000,
      "content": 400000000,
      "events": 300000000,
      "partnerships": 200000000
    }
  }
}

// Requires:
// - 30% quorum
// - 65% approval
```

---

## Voting Power Calculation

```typescript
// Base voting power from governance level
const basePower = stakeholder.governance_level; // 1-10

// Reputation multiplier
const reputationMultiplier =
  reputationScore >= 90 ? 2.0 :    // Sage
  reputationScore >= 80 ? 1.5 :    // Expert
  reputationScore >= 70 ? 1.0 :    // Trusted
  reputationScore >= 60 ? 0.8 :    // Member
  0.5;                              // Novice

// Effective voting power
const effectivePower = basePower * reputationMultiplier;

// Example:
// - Governance level: 7
// - Reputation score: 85 (Expert tier)
// - Effective voting power: 7 * 1.5 = 10.5
```

---

## Related Endpoints

- [GET /v1/ledger](./ledger.md) — Treasury balance for funding proposals
- [POST /v1/equity/grants](./equity.md) — Equity grants from approved proposals
- [GET /v1/revenue/distribution](./revenue.md) — Revenue split for stakeholders
- [GET /v1/rbac/permissions](./rbac.md) — Role-based permissions

---

## Next Steps

- [Ledger API](./ledger.md) — Double-entry accounting system
- [Equity API](./equity.md) — Equity management and cap tables
- [Revenue API](./revenue.md) — 6-way revenue distribution
- [Funding API](./funding.md) — Quadratic funding rounds
