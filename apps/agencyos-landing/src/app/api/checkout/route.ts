import { NextRequest, NextResponse } from 'next/server';
import { createCheckoutSession } from '@/lib/polar-checkout-client';
import { CheckoutSchema } from '@/lib/schemas/checkout';
import { ApiError, handleRouteError } from '@/lib/api-errors';
import { isRateLimited, getClientIp } from '@/lib/rate-limiter';

export async function POST(req: NextRequest) {
  try {
    const clientIp = getClientIp(req.headers);
    if (isRateLimited(clientIp)) {
      throw new ApiError('Too many requests', 'RATE_LIMITED', 429);
    }

    const body = await req.json();
    const { priceId, customerEmail, locale: bodyLocale } = CheckoutSchema.parse(body);

    const baseUrl = req.headers.get('origin') || 'http://localhost:3000';
    const locale = bodyLocale || req.headers.get('x-locale') || 'en';

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
  } catch (error: unknown) {
    return handleRouteError(error);
  }
}
