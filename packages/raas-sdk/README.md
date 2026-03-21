# @mekong/raas-sdk

Typed TypeScript SDK for the [Mekong RaaS Gateway](https://raas-gateway.agencyos-openclaw.workers.dev).

- Zero external dependencies (native `fetch`)
- Full type coverage for all endpoints
- Built-in retry with exponential backoff (3 attempts)
- Typed error classes per HTTP status

## Install

```bash
npm install @mekong/raas-sdk
```

## Quick Start

```typescript
import { MekongClient } from '@mekong/raas-sdk';

// Auth via JWT (after signup)
const client = new MekongClient({ jwt: 'your-jwt-token' });

// Auth via API key
const client = new MekongClient({ apiKey: 'mk_live_...' });
```

## Signup & Auth

```typescript
const client = new MekongClient();
const { token, tenant } = await client.tenants.signup({
  name: 'Acme Corp',
  email: 'admin@acme.com',
});
client.setJwt(token); // auto-auth subsequent calls
```

## Missions

```typescript
// Submit
const mission = await client.missions.submit({
  goal: 'Write a blog post about AI trends in 2026',
  complexity: 'standard',
});

// Poll until done
let result = await client.missions.poll(mission.id);
while (result.status === 'pending' || result.status === 'processing') {
  await new Promise(r => setTimeout(r, 2000));
  result = await client.missions.poll(mission.id);
}

// Get full result
const full = await client.missions.get(mission.id);
console.log(full.result);

// Batch submit (pro+)
const batch = await client.missions.batch({
  missions: [
    { goal: 'Task 1', complexity: 'simple' },
    { goal: 'Task 2', complexity: 'complex' },
  ],
});

// Share publicly
const { share_url } = await client.missions.share(mission.id);
```

## Credits

```typescript
const { balance } = await client.credits.getBalance();

// Pre-check cost before submitting
const check = await client.credits.check({ complexity: 'complex' });
if (check.can_proceed) { /* ... */ }

// Redeem coupon
await client.credits.redeem({ code: 'WELCOME50' });
```

## Billing

```typescript
const pricing = await client.billing.getPricing();
const packs = await client.billing.getCreditPacks();

const { checkout_url } = await client.billing.createCheckout({
  pack_id: packs[0].id,
  success_url: 'https://app.example.com/success',
});
```

## Marketplace

```typescript
const results = await client.marketplace.search({ q: 'blog post', limit: 20 });
const featured = await client.marketplace.getFeatured();
await client.marketplace.submitReview(missionId, { rating: 5, comment: 'Great!' });
```

## Tenants

```typescript
const profile = await client.tenants.getProfile();
await client.tenants.updateSettings({ webhook_url: 'https://...' });

const { key } = await client.tenants.createApiKey({ name: 'CI bot' });
const keys = await client.tenants.listApiKeys();
await client.tenants.revokeApiKey(keys[0].id);
```

## Licenses

```typescript
const license = await client.licenses.create({ type: 'team', email: 'dev@acme.com' });
const { valid } = await client.licenses.verify(license.key);
await client.licenses.activate(license.key);
```

## Status & Health

```typescript
const health = await client.health.check();
const sys = await client.status.get();
const incidents = await client.status.getIncidents();
```

## Error Handling

```typescript
import {
  MekongApiError,
  MekongAuthError,
  MekongInsufficientCreditsError,
  MekongRateLimitError,
  MekongNetworkError,
} from '@mekong/raas-sdk';

try {
  await client.missions.submit({ goal: '...' });
} catch (err) {
  if (err instanceof MekongInsufficientCreditsError) {
    console.log('Top up credits at https://mekong-raas.pages.dev');
  } else if (err instanceof MekongAuthError) {
    console.log('Invalid or expired token');
  } else if (err instanceof MekongRateLimitError) {
    console.log('Slow down — rate limited');
  } else if (err instanceof MekongApiError) {
    console.log(`API error ${err.status}: ${err.message}`);
  } else if (err instanceof MekongNetworkError) {
    console.log('Network failure, check connectivity');
  }
}
```

## Configuration

```typescript
const client = new MekongClient({
  baseUrl: 'https://raas-gateway.agencyos-openclaw.workers.dev', // default
  jwt: 'your-jwt',
  apiKey: 'mk_live_...',
  maxRetries: 3,    // retry on 5xx (default: 3)
  timeoutMs: 30000, // request timeout ms (default: 30s)
});
```

## License

MIT
