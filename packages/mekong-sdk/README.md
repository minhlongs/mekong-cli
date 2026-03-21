# @mekong/sdk

TypeScript SDK for the [Mekong RaaS Gateway](https://raas.agencyos.network) — zero dependencies, native fetch.

## Install

```bash
npm install @mekong/sdk
# or
pnpm add @mekong/sdk
```

## Quick Start

```ts
import { MekongClient } from '@mekong/sdk'

// Authenticate with API key
const client = new MekongClient({
  apiKey: 'mk_live_...',
})

// Submit a mission
const mission = await client.submitMission({
  goal: 'Write a landing page for a SaaS product',
  complexity: 'medium',
})

console.log(mission.id, mission.status, mission.creditsCost)
```

## Authentication

Two auth modes supported — use one or the other:

```ts
// Bearer token (from login/signup)
const client = new MekongClient({ token: 'eyJ...' })

// API key
const client = new MekongClient({ apiKey: 'mk_live_...' })

// Update auth after construction
client.setToken('eyJ...')
client.setApiKey('mk_live_...')
```

## API Reference

### Auth

```ts
// Register new tenant (auto-sets token)
const res = await client.signup({ name: 'Acme', email: 'hello@acme.com', ref: 'FRIEND' })
// res: { tenantId, token, credits, referralCode }

// Login (auto-sets token)
const res = await client.login({ email: 'hello@acme.com' })
// res: { tenantId, token, tier }
```

### Tenant Profile

```ts
const profile = await client.getProfile()
// { id, name, email, tier, balance }

const referrals = await client.getReferrals()
// { referralCode, totalReferred, creditsEarned }

const digest = await client.getDigest()
// { period, missions, balance, recentGoals }

const upgrade = await client.getUpgrade()
// { checkoutUrl, tier }
```

### API Keys

```ts
const { keyId, apiKey } = await client.createApiKey({ name: 'Production' })

const { keys } = await client.listApiKeys()
// keys: [{ id, name, revoked }]

await client.revokeApiKey(keyId)
```

### Missions

```ts
// Submit
const mission = await client.submitMission({
  goal: 'Build a REST API in Node.js',
  complexity: 'high',       // 'low' | 'medium' | 'high'
  project: 'my-project',
  model: 'claude-3-5-sonnet',
  callback_url: 'https://myapp.com/webhooks/mission',
})

// Get single
const mission = await client.getMission('mission_abc123')

// List with filters
const { missions, total } = await client.listMissions({
  status: 'completed',
  limit: 20,
  offset: 0,
})

// Poll (long-poll until complete)
const result = await client.pollMission('mission_abc123')

// Cancel / share
await client.cancelMission('mission_abc123')
const { shareUrl } = await client.shareMission('mission_abc123')

// Batch submit
const batch = await client.batchMissions({
  goals: [
    { goal: 'Write blog post', complexity: 'low' },
    { goal: 'Design database schema', complexity: 'high' },
  ],
})
// { submitted, failed, missions }
```

### Credits

```ts
const credits = await client.getCredits()
// { balance, totalEarned, totalSpent }

const cost = await client.checkCost({ complexity: 'high' })
// { cost, balance, sufficient }

const { checkoutUrl } = await client.purchaseCredits({ pack: 'starter' })
```

### Analytics

```ts
const analytics = await client.getAnalytics()
// { summary, byComplexity, byStatus, daily }
```

### Public Endpoints (no auth)

```ts
import { MekongClient } from '@mekong/sdk'

const stats = await MekongClient.getStats()
// { totalMissions, totalTenants, uptime }

const templates = await MekongClient.getTemplates()
// MissionTemplate[]

const pricing = await MekongClient.getPricing()
// { packs: [{ id, credits, price, label }] }
```

## Error Handling

All methods throw `MekongError` on failure:

```ts
import { MekongClient, MekongError } from '@mekong/sdk'

try {
  await client.submitMission({ goal: 'Do something' })
} catch (err) {
  if (err instanceof MekongError) {
    console.error(err.message)  // human-readable message
    console.error(err.status)   // HTTP status (0 = network/timeout)
    console.error(err.code)     // e.g. 'HTTP_402', 'TIMEOUT', 'NETWORK_ERROR'
    console.error(err.data)     // raw API response body
  }
}
```

## Configuration

```ts
const client = new MekongClient({
  baseUrl: 'https://raas.agencyos.network', // default
  token: 'eyJ...',
  apiKey: 'mk_live_...',
  timeout: 30000,  // ms, default 30s
})
```

## TypeScript

All request and response types are exported:

```ts
import type {
  Mission,
  MissionStatus,
  MissionComplexity,
  SubmitMissionRequest,
  MekongClientConfig,
} from '@mekong/sdk'
```
