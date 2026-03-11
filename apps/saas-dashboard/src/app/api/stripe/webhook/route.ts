import { NextResponse } from 'next/server';
import { headers } from 'next/headers';
import Stripe from 'stripe';

const webhookSecret = process.env.STRIPE_WEBHOOK_SECRET || '';

// Lazy init Stripe to avoid build-time execution
function getStripe(): Stripe {
  return new Stripe(process.env.STRIPE_SECRET_KEY || '', {
    apiVersion: '2025-02-24.acacia',
    typescript: true,
  });
}

async function buffer(readable: ReadableStream<Uint8Array>) {
  const chunks: Uint8Array[] = [];
  const reader = readable.getReader();
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    chunks.push(value);
  }
  return Buffer.concat(chunks);
}

export async function POST(request: Request) {
  const stripe = getStripe();
  const body = await buffer(request.body!);
  const headersList = await headers();
  const signature = headersList.get('stripe-signature')!;

  let event: Stripe.Event;

  try {
    event = stripe.webhooks.constructEvent(body, signature, webhookSecret);
  } catch (err) {
    console.error('Webhook signature verification failed:', err);
    return NextResponse.json(
      { error: 'Webhook signature verification failed' },
      { status: 400 }
    );
  }

  switch (event.type) {
    case 'checkout.session.completed': {
      const session = event.data.object as Stripe.Checkout.Session;
      console.log('Checkout completed:', {
        sessionId: session.id,
        customerId: session.customer,
        subscriptionId: session.subscription,
      });

      // TODO: Update subscription in database
      // await updateSubscription({
      //   stripeSubscriptionId: session.subscription as string,
      //   stripeCustomerId: session.customer as string,
      //   userId: session.metadata?.userId,
      //   plan: session.metadata?.plan,
      //   status: 'active',
      // });
      break;
    }

    case 'customer.subscription.updated': {
      const subscription = event.data.object as Stripe.Subscription;
      console.log('Subscription updated:', {
        id: subscription.id,
        status: subscription.status,
      });

      // TODO: Update subscription status in database
      // await updateSubscriptionStatus({
      //   stripeSubscriptionId: subscription.id,
      //   status: subscription.status,
      //   currentPeriodEnd: new Date(subscription.current_period_end * 1000),
      // });
      break;
    }

    case 'customer.subscription.deleted': {
      const subscription = event.data.object as Stripe.Subscription;
      console.log('Subscription deleted:', subscription.id);

      // TODO: Mark subscription as canceled
      // await cancelSubscription(subscription.id);
      break;
    }

    case 'invoice.payment_succeeded': {
      const invoice = event.data.object as Stripe.Invoice;
      console.log('Payment succeeded:', {
        invoiceId: invoice.id,
        amount: invoice.amount_paid,
      });

      // TODO: Record successful payment
      // await recordPayment(invoice);
      break;
    }

    case 'invoice.payment_failed': {
      const invoice = event.data.object as Stripe.Invoice;
      const paymentIntent = typeof invoice.payment_intent === 'string'
        ? null
        : invoice.payment_intent;
      console.log('Payment failed:', {
        invoiceId: invoice.id,
        reason: paymentIntent?.last_payment_error?.message,
      });

      // TODO: Handle failed payment (notify user, retry logic)
      // await handleFailedPayment(invoice);
      break;
    }

    default:
      console.log('Unhandled webhook event:', event.type);
  }

  return NextResponse.json({ received: true });
}
