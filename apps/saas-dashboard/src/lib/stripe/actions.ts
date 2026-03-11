'use server';

import { stripe, STRIPE_PRICES } from './server';
import { auth } from '@/lib/auth/config';
import { cookies } from 'next/headers';

export async function createCheckoutSession(plan: 'PRO' | 'ENTERPRISE') {
  try {
    const session = await auth.api.getSession({
      headers: new Headers(),
    });

    if (!session?.user) {
      return { error: 'Authentication required' };
    }

    const priceId = STRIPE_PRICES[plan];
    if (!priceId) {
      return { error: 'Invalid plan' };
    }

    const checkoutSession = await stripe.checkout.sessions.create({
      mode: 'subscription',
      payment_method_types: ['card'],
      line_items: [
        {
          price: priceId,
          quantity: 1,
        },
      ],
      success_url: `${process.env.NEXT_PUBLIC_APP_URL}/dashboard?session_id={CHECKOUT_SESSION_ID}`,
      cancel_url: `${process.env.NEXT_PUBLIC_APP_URL}/pricing`,
      client_reference_id: session.user.id,
      customer_email: session.user.email,
      metadata: {
        userId: session.user.id,
        plan,
      },
    });

    return { url: checkoutSession.url };
  } catch (error) {
    console.error('Checkout error:', error);
    return { error: 'Failed to create checkout session' };
  }
}

export async function createCustomerPortalSession() {
  try {
    const session = await auth.api.getSession({
      headers: new Headers(),
    });

    if (!session?.user) {
      return { error: 'Authentication required' };
    }

    // Get Stripe customer ID from database (implement later)
    // For now, return error
    return { error: 'No active subscription found' };

    // TODO: Implement when subscription table is ready
    // const customer = await getCustomerByUserId(session.user.id);
    // if (!customer) return { error: 'No customer found' };

    // const portalSession = await stripe.billingPortal.sessions.create({
    //   customer: customer.stripeCustomerId,
    //   return_url: `${process.env.NEXT_PUBLIC_APP_URL}/dashboard`,
    // });

    // return { url: portalSession.url };
  } catch (error) {
    console.error('Portal error:', error);
    return { error: 'Failed to create portal session' };
  }
}
