import { NextResponse } from 'next/server';
import { createCustomerPortalSession } from '@/lib/stripe/actions';

export async function POST() {
  try {
    const result = await createCustomerPortalSession();

    if (result.error || !result.url) {
      return NextResponse.json({ error: result?.error || 'No URL available' }, { status: 400 });
    }

    return NextResponse.json({ url: result.url });
  } catch (error) {
    console.error('Portal API error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
