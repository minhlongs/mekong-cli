import { NextRequest, NextResponse } from 'next/server';
import { verifyWebhookSignature } from '@/lib/polar-checkout-client';
import { headers } from 'next/headers';

export async function POST(req: NextRequest) {
  try {
    const payload = await req.text();
    const headersList = await headers();
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
