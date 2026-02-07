# Phase 06: Hub Integration

## Overview

**Priority:** P1 (Critical)
**Status:** Pending
**Effort:** 4 hours

Integrate AgencyOS Hub SDKs including `@agencyos/money` (Polar.sh checkout), `@agencyos/vibe-analytics` (telemetry), and other relevant packages from the monorepo.

## Context Links

- Phase 04: [Pricing & Conversion](./phase-04-pricing-conversion.md)
- Phase 05: [i18n & SEO](./phase-05-i18n-seo.md)
- Hub Architecture: `../../packages/README.md`
- Money Layer: `../../packages/business/money/`
- Analytics: `../../packages/tooling/analytics/`

## Key Insights

- Hub SDKs provide battle-tested payment/analytics
- Polar.sh Standard Webhooks for checkout flow
- Vibe Analytics tracks conversion funnel
- Hub integration reduces 80% boilerplate code
- Shared types ensure consistency across monorepo

## Requirements

### Functional
- Polar.sh checkout flow via @agencyos/money
- Event tracking via @agencyos/vibe-analytics
- Conversion funnel monitoring
- Payment webhook handling
- Error tracking integration
- User session tracking

### Non-Functional
- SDK bundle size <50KB (tree-shaking)
- Analytics events <100ms overhead
- Webhook response time <500ms
- Type safety across all integrations
- Environment-based config (dev/prod)

## Architecture

```
apps/agencyos-landing/
├── package.json                    # MODIFY: Add Hub deps
├── src/
│   ├── lib/
│   │   ├── money.ts                # NEW: Polar.sh client
│   │   ├── analytics.ts            # NEW: Analytics client
│   │   └── env.ts                  # NEW: Env validation
│   ├── app/
│   │   └── api/
│   │       ├── checkout/route.ts   # REFACTOR: Use @agencyos/money
│   │       └── webhooks/
│   │           └── polar/route.ts  # NEW: Webhook handler
│   └── components/
│       └── providers/
│           └── analytics-provider.tsx  # NEW: Analytics context

packages/business/money/             # Hub SDK (reference)
packages/tooling/analytics/          # Hub SDK (reference)
```

## Related Code Files

**To Create:**
- `src/lib/money.ts`
- `src/lib/analytics.ts`
- `src/lib/env.ts`
- `src/app/api/webhooks/polar/route.ts`
- `src/components/providers/analytics-provider.tsx`

**To Refactor:**
- `src/app/api/checkout/route.ts` - Use @agencyos/money
- `src/components/checkout-button.tsx` - Add analytics events

**To Install:**
- `@agencyos/money`
- `@agencyos/vibe-analytics`
- `@agencyos/shared` (types)
- `zod` (validation)

## Implementation Steps

### 1. Install Hub Dependencies (15min)

```bash
cd apps/agencyos-landing

# Add workspace dependencies
npm install @agencyos/money@workspace:* \
            @agencyos/vibe-analytics@workspace:* \
            @agencyos/shared@workspace:*

# Add third-party deps
npm install zod micro @t3-oss/env-nextjs
```

Update `package.json`:
```json
{
  "dependencies": {
    "@agencyos/money": "workspace:*",
    "@agencyos/vibe-analytics": "workspace:*",
    "@agencyos/shared": "workspace:*",
    "zod": "^3.22.4",
    "micro": "^10.0.1",
    "@t3-oss/env-nextjs": "^0.7.0"
  }
}
```

### 2. Configure Environment Variables (30min)

`src/lib/env.ts`:
```typescript
import { createEnv } from "@t3-oss/env-nextjs";
import { z } from "zod";

export const env = createEnv({
  server: {
    // Polar.sh
    POLAR_ACCESS_TOKEN: z.string().min(1),
    POLAR_WEBHOOK_SECRET: z.string().min(1),
    POLAR_ORGANIZATION_ID: z.string().min(1),

    // Analytics
    ANALYTICS_WRITE_KEY: z.string().optional(),

    // Database (if needed for webhooks)
    DATABASE_URL: z.string().url().optional(),
  },
  client: {
    NEXT_PUBLIC_POLAR_PRICE_STARTER: z.string().min(1),
    NEXT_PUBLIC_POLAR_PRICE_PRO: z.string().min(1),
    NEXT_PUBLIC_ANALYTICS_HOST: z.string().url().optional(),
  },
  runtimeEnv: {
    // Server
    POLAR_ACCESS_TOKEN: process.env.POLAR_ACCESS_TOKEN,
    POLAR_WEBHOOK_SECRET: process.env.POLAR_WEBHOOK_SECRET,
    POLAR_ORGANIZATION_ID: process.env.POLAR_ORGANIZATION_ID,
    ANALYTICS_WRITE_KEY: process.env.ANALYTICS_WRITE_KEY,
    DATABASE_URL: process.env.DATABASE_URL,

    // Client
    NEXT_PUBLIC_POLAR_PRICE_STARTER: process.env.NEXT_PUBLIC_POLAR_PRICE_STARTER,
    NEXT_PUBLIC_POLAR_PRICE_PRO: process.env.NEXT_PUBLIC_POLAR_PRICE_PRO,
    NEXT_PUBLIC_ANALYTICS_HOST: process.env.NEXT_PUBLIC_ANALYTICS_HOST,
  },
});
```

`.env.local` (example):
```env
# Polar.sh Configuration
POLAR_ACCESS_TOKEN=polar_at_xxx
POLAR_WEBHOOK_SECRET=whsec_xxx
POLAR_ORGANIZATION_ID=org_xxx

NEXT_PUBLIC_POLAR_PRICE_STARTER=price_xxx
NEXT_PUBLIC_POLAR_PRICE_PRO=price_yyy

# Analytics (optional)
ANALYTICS_WRITE_KEY=
NEXT_PUBLIC_ANALYTICS_HOST=https://analytics.agencyos.dev
```

### 3. Setup Money Layer Client (45min)

`src/lib/money.ts`:
```typescript
import { PolarClient } from '@agencyos/money';
import { env } from './env';

export const polarClient = new PolarClient({
  accessToken: env.POLAR_ACCESS_TOKEN,
  organizationId: env.POLAR_ORGANIZATION_ID,
  server: process.env.NODE_ENV === 'production'
    ? 'https://api.polar.sh'
    : 'https://sandbox-api.polar.sh',
});

export type CheckoutSessionParams = {
  priceId: string;
  successUrl: string;
  customerEmail?: string;
  metadata?: Record<string, string>;
};

export async function createCheckoutSession(params: CheckoutSessionParams) {
  return polarClient.checkouts.create({
    price_id: params.priceId,
    success_url: params.successUrl,
    customer_email: params.customerEmail,
    metadata: params.metadata,
  });
}

export async function verifyWebhookSignature(
  payload: string,
  signature: string
): Promise<boolean> {
  return polarClient.webhooks.verify(payload, signature, env.POLAR_WEBHOOK_SECRET);
}
```

### 4. Refactor Checkout API Route (30min)

`src/app/api/checkout/route.ts`:
```typescript
import { NextRequest, NextResponse } from 'next/server';
import { createCheckoutSession } from '@/lib/money';
import { z } from 'zod';

const CheckoutSchema = z.object({
  priceId: z.string().min(1),
  customerEmail: z.string().email().optional(),
});

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { priceId, customerEmail } = CheckoutSchema.parse(body);

    const baseUrl = req.headers.get('origin') || 'http://localhost:3000';
    const locale = req.headers.get('x-locale') || 'en';

    const session = await createCheckoutSession({
      priceId,
      customerEmail,
      successUrl: `${baseUrl}/${locale}/success?session_id={CHECKOUT_SESSION_ID}`,
      metadata: {
        source: 'landing-page',
        locale,
      },
    });

    return NextResponse.json({ url: session.url });
  } catch (error) {
    console.error('Checkout error:', error);

    if (error instanceof z.ZodError) {
      return NextResponse.json(
        { error: 'Invalid request data', details: error.errors },
        { status: 400 }
      );
    }

    return NextResponse.json(
      { error: 'Failed to create checkout session' },
      { status: 500 }
    );
  }
}
```

### 5. Implement Webhook Handler (1h)

`src/app/api/webhooks/polar/route.ts`:
```typescript
import { NextRequest, NextResponse } from 'next/server';
import { verifyWebhookSignature } from '@/lib/money';
import { headers } from 'next/headers';

export async function POST(req: NextRequest) {
  try {
    const payload = await req.text();
    const headersList = headers();
    const signature = headersList.get('polar-signature');

    if (!signature) {
      return NextResponse.json(
        { error: 'Missing signature' },
        { status: 401 }
      );
    }

    const isValid = await verifyWebhookSignature(payload, signature);
    if (!isValid) {
      return NextResponse.json(
        { error: 'Invalid signature' },
        { status: 401 }
      );
    }

    const event = JSON.parse(payload);

    // Handle different event types
    switch (event.type) {
      case 'checkout.completed':
        await handleCheckoutCompleted(event.data);
        break;

      case 'subscription.created':
        await handleSubscriptionCreated(event.data);
        break;

      case 'subscription.updated':
        await handleSubscriptionUpdated(event.data);
        break;

      case 'subscription.cancelled':
        await handleSubscriptionCancelled(event.data);
        break;

      default:
        console.log(`Unhandled event type: ${event.type}`);
    }

    return NextResponse.json({ received: true });
  } catch (error) {
    console.error('Webhook error:', error);
    return NextResponse.json(
      { error: 'Webhook processing failed' },
      { status: 500 }
    );
  }
}

async function handleCheckoutCompleted(data: any) {
  console.log('Checkout completed:', data);
  // TODO: Send confirmation email, provision access, etc.
}

async function handleSubscriptionCreated(data: any) {
  console.log('Subscription created:', data);
  // TODO: Grant user access, send welcome email
}

async function handleSubscriptionUpdated(data: any) {
  console.log('Subscription updated:', data);
  // TODO: Update user permissions
}

async function handleSubscriptionCancelled(data: any) {
  console.log('Subscription cancelled:', data);
  // TODO: Schedule access revocation, send exit survey
}
```

### 6. Setup Analytics Client (30min)

`src/lib/analytics.ts`:
```typescript
import { AnalyticsClient } from '@agencyos/vibe-analytics';
import { env } from './env';

export const analytics = new AnalyticsClient({
  writeKey: env.ANALYTICS_WRITE_KEY || '',
  host: env.NEXT_PUBLIC_ANALYTICS_HOST,
  flushAt: 20,
  flushInterval: 10000,
});

export const trackEvent = (event: string, properties?: Record<string, any>) => {
  if (typeof window === 'undefined') return;

  analytics.track({
    event,
    properties: {
      ...properties,
      url: window.location.href,
      path: window.location.pathname,
      referrer: document.referrer,
      timestamp: new Date().toISOString(),
    },
  });
};

export const trackPageView = (path?: string) => {
  if (typeof window === 'undefined') return;

  analytics.page({
    path: path || window.location.pathname,
    url: window.location.href,
    referrer: document.referrer,
  });
};

export const identifyUser = (userId: string, traits?: Record<string, any>) => {
  analytics.identify({
    userId,
    traits,
  });
};
```

### 7. Create Analytics Provider (30min)

`src/components/providers/analytics-provider.tsx`:
```typescript
"use client";

import { useEffect } from 'react';
import { usePathname, useSearchParams } from 'next/navigation';
import { trackPageView } from '@/lib/analytics';

export function AnalyticsProvider({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const searchParams = useSearchParams();

  useEffect(() => {
    // Track initial page view
    trackPageView(pathname);
  }, [pathname, searchParams]);

  return <>{children}</>;
}
```

Update `src/app/[locale]/layout.tsx`:
```typescript
import { AnalyticsProvider } from '@/components/providers/analytics-provider';

export default async function LocaleLayout({ children, params }) {
  // ... existing code

  return (
    <html lang={locale}>
      <body>
        <NextIntlClientProvider messages={messages}>
          <AnalyticsProvider>
            {children}
          </AnalyticsProvider>
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
```

### 8. Add Analytics Events to Components (45min)

Update `src/components/checkout-button.tsx`:
```typescript
"use client";

import { useState } from 'react';
import { trackEvent } from '@/lib/analytics';

export function CheckoutButton({
  priceId,
  children,
  tier,
}: {
  priceId: string;
  children: React.ReactNode;
  tier?: string;
}) {
  const [loading, setLoading] = useState(false);

  const handleCheckout = async () => {
    setLoading(true);

    trackEvent('Checkout Started', {
      tier,
      priceId,
    });

    try {
      const res = await fetch('/api/checkout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ priceId }),
      });

      const { url } = await res.json();

      trackEvent('Checkout Session Created', {
        tier,
        priceId,
      });

      window.location.href = url;
    } catch (error) {
      console.error('Checkout failed:', error);

      trackEvent('Checkout Failed', {
        tier,
        priceId,
        error: error.message,
      });

      setLoading(false);
    }
  };

  return (
    <div onClick={handleCheckout}>
      {children}
    </div>
  );
}
```

Add tracking to key interactions:
- Hero CTA clicks
- Feature card views
- Pricing tier selections
- FAQ expansions
- Language switches

## Todo List

- [ ] Install Hub SDK dependencies
- [ ] Create env.ts with validation
- [ ] Setup .env.local with Polar.sh credentials
- [ ] Create money.ts client wrapper
- [ ] Refactor checkout API route
- [ ] Implement Polar webhook handler
- [ ] Create analytics.ts client
- [ ] Create AnalyticsProvider component
- [ ] Add analytics events to CheckoutButton
- [ ] Add analytics to Hero CTA
- [ ] Add analytics to pricing tier selection
- [ ] Test checkout flow end-to-end
- [ ] Test webhook signature verification
- [ ] Verify analytics events in dashboard
- [ ] Configure Polar webhook URL in dashboard
- [ ] Test error handling (invalid price ID)
- [ ] Verify event payloads in analytics

## Success Criteria

- ✅ Checkout flow completes successfully
- ✅ Webhook signature validation works
- ✅ All webhook events handled (checkout, subscription)
- ✅ Analytics tracks page views automatically
- ✅ Conversion funnel events recorded
- ✅ Hub SDKs properly tree-shaken (<50KB)
- ✅ Type safety across all integrations
- ✅ Environment variables validated on build
- ✅ Error handling for failed payments
- ✅ Webhook responses <500ms

## Risk Assessment

**Risk:** Webhook signature mismatch
**Mitigation:** Test with Polar CLI webhook forwarding, verify secret

**Risk:** Analytics blocking page load
**Mitigation:** Async loading, timeout on slow requests

**Risk:** Missing environment variables in production
**Mitigation:** Use @t3-oss/env for build-time validation

**Risk:** Hub SDK version mismatch
**Mitigation:** Use workspace:* protocol, lock versions

## Security Considerations

- Webhook signature verification mandatory
- Environment secrets never exposed to client
- Rate limiting on checkout endpoint
- CSRF protection on API routes
- PII data handling (customer emails)
- Compliance: Store minimal payment data

## Next Steps

→ Proceed to Phase 07: Verification & Deployment
