import { NextResponse } from 'next/server';
import { createCheckoutSession } from '@/lib/stripe/actions';

export async function POST(request: Request) {
  try {
    const { plan } = await request.json();

    if (!plan || !['PRO', 'ENTERPRISE'].includes(plan)) {
      return NextResponse.json(
        { error: 'Invalid plan. Must be PRO or ENTERPRISE' },
        { status: 400 }
      );
    }

    const result = await createCheckoutSession(plan as 'PRO' | 'ENTERPRISE');

    if (result.error) {
      return NextResponse.json({ error: result.error }, { status: 400 });
    }

    return NextResponse.json({ url: result.url });
  } catch (error) {
    console.error('Checkout API error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
