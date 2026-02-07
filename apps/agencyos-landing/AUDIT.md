src/app/api/webhooks/polar/route.ts:47:        console.log(`Unhandled event type: ${event.type}`);
src/app/api/webhooks/polar/route.ts:60:async function handleCheckoutCompleted(data: any) {
src/app/api/webhooks/polar/route.ts:61:  console.log('Checkout completed:', data);
src/app/api/webhooks/polar/route.ts:62:  // TODO: Send confirmation email, provision access, etc.
src/app/api/webhooks/polar/route.ts:65:async function handleSubscriptionCreated(data: any) {
src/app/api/webhooks/polar/route.ts:66:  console.log('Subscription created:', data);
src/app/api/webhooks/polar/route.ts:67:  // TODO: Grant user access, send welcome email
src/app/api/webhooks/polar/route.ts:70:async function handleSubscriptionUpdated(data: any) {
src/app/api/webhooks/polar/route.ts:71:  console.log('Subscription updated:', data);
src/app/api/webhooks/polar/route.ts:72:  // TODO: Update user permissions
src/app/api/webhooks/polar/route.ts:75:async function handleSubscriptionCancelled(data: any) {
src/app/api/webhooks/polar/route.ts:76:  console.log('Subscription cancelled:', data);
src/app/api/webhooks/polar/route.ts:77:  // TODO: Schedule access revocation, send exit survey
src/lib/polar-checkout-client.ts:13:  console.log('Creating checkout session:', params);
src/lib/polar-checkout-client.ts:26:  console.log('Verifying webhook signature');
src/lib/vibe-analytics-client.ts:7:    console.log('Track event:', event);
src/lib/vibe-analytics-client.ts:11:    console.log('Track page:', data);
src/lib/vibe-analytics-client.ts:14:    console.log('Identify user:', data);
