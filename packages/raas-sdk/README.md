# @mekong/raas-sdk

TypeScript SDK for the Mekong RaaS (Robot-as-a-Service) API.

- Zero external dependencies (native `fetch`)
- Full type coverage for all endpoints
- Built-in retry with exponential backoff (default: 3 attempts)
- Typed error classes per HTTP status

## Installation

```bash
npm install @mekong/raas-sdk
```

## Quick Start

```typescript
import { MekongClient } from '@mekong/raas-sdk';

// Create client and signup
const client = new MekongClient();
const { token, tenant } = await client.tenants.signup({
  name: 'Acme Corp',
  email: 'admin@acme.com',
});
client.setJwt(token); // auto-auth all subsequent requests

// Submit a mission
const mission = await client.missions.submit({
  goal: 'Write a blog post about AI trends in 2026',
  complexity: 'standard',
});

// Poll until done
let poll = await client.missions.poll(mission.id);
while (poll.status === 'pending' || poll.status === 'processing') {
  await new Promise(r => setTimeout(r, 2000));
  poll = await client.missions.poll(mission.id);
}

// Get full result
const full = await client.missions.get(mission.id);
console.log(full.result);
```

## Authentication

Two auth methods — mutually exclusive:

```typescript
// JWT (recommended after signup/login)
const client = new MekongClient({ jwt: 'eyJhbGciOiJ...' });

// API Key (for server-to-server)
const client = new MekongClient({ apiKey: 'mk_live_...' });

// Update JWT dynamically after login
client.setJwt(newToken);
```

## Resources

### Missions

```typescript
client.missions.submit(params)        // Submit new mission (1–5 MCU)
client.missions.get(id)               // Get mission + full result
client.missions.list(params?)         // List missions (paginated)
client.missions.poll(id)              // Lightweight status poll
client.missions.cancel(id)            // Cancel + refund credits
client.missions.share(id)             // Generate public share URL
client.missions.batch(params)         // Batch submit (pro+)
client.missions.listTemplates(cat?)   // Browse mission templates
```

### Tenants

```typescript
client.tenants.signup(params)         // Create account → JWT + 10 credits
client.tenants.getProfile()           // Get tenant info
client.tenants.updateSettings(params) // Update webhook URL, notifications
client.tenants.createApiKey(params?)  // Create API key
client.tenants.listApiKeys()          // List all API keys
client.tenants.revokeApiKey(id)       // Revoke API key
client.tenants.getUsage()             // Usage stats for current period
client.tenants.getInvoices(params?)   // Credit transaction history
client.tenants.extendTrial()          // Extend trial period
```

### Credits

```typescript
client.credits.getBalance()           // Current balance + total spent
client.credits.check(params)          // Pre-check cost before submitting
client.credits.getHistory()           // Transaction history
client.credits.redeem(params)         // Redeem coupon code
client.credits.submitFeedback(params) // Submit feedback for bonus credits
```

### Billing

```typescript
client.billing.getPricing()           // Subscription tiers + pricing
client.billing.getCreditPacks()       // One-time credit packs
client.billing.createCheckout(params) // Create Stripe checkout session
```

### Marketplace

```typescript
client.marketplace.search(params?)          // Search public missions
client.marketplace.getFeatured()            // Featured/trending missions
client.marketplace.getStats()               // Platform-wide stats
client.marketplace.getLeaderboard()         // Top referrers
client.marketplace.getReviews(missionId)    // Reviews for a mission
client.marketplace.submitReview(id, params) // Submit a review
```

### System

```typescript
client.health.check()           // Basic health check
client.health.deep()            // Deep health + component checks
client.status.get()             // System status page data
client.status.getIncidents()    // Active + recent incidents
client.public.getStats()        // Public platform stats
client.public.joinWaitlist(email) // Join waitlist
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
  maxRetries: 3,    // retry on 5xx/network errors (default: 3)
  timeoutMs: 30000, // request timeout in ms (default: 30s)
});
```

## License

MIT
