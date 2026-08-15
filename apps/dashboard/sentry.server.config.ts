/**
 * Sentry Server Configuration
 *
 * This file is used to configure Sentry for Node.js server-side rendering
 * and API routes. It captures server errors and performance metrics.
 */
import * as Sentry from "@sentry/nextjs";

export const getServerSentryConfig = () => ({
  // Automatically capture unhandled exceptions
  autoSessionTracking: true,
  // Sample rate for transactions (adjust based on traffic/cost)
  tracesSampleRate: 1.0, // 100% in dev, use env var in prod
  // Record profiles for performance analysis
  profilesSampleRate: 0.1, // 10% of transactions
  // Include request data in events (scrubbed by beforeSend)
  includeRequestContext: true,
  // Breadcrumbs
  beforeBreadcrumb(breadcrumb) {
    // Filter out noisy breadcrumbs
    if (breadcrumb.category === "console") {
      const message = breadcrumb.message || "";
      const noisyPatterns = [
        /GraphQL/i,
        /Apollo/i,
        /\[HPM\]/, // Hot module replacement
      ];
      if (noisyPatterns.some((re) => re.test(message))) {
        return null;
      }
    }
    return breadcrumb;
  },
  // Scrub sensitive data before sending
  beforeSend(event, hint) {
    // Scrub request headers
    if (event.request?.headers) {
      const sensitiveHeaders = ["authorization", "cookie", "x-api-key", "x-idempotency-key"];
      for (const header of sensitiveHeaders) {
        if (event.request.headers[header]) {
          event.request.headers[header] = "[Filtered]";
        }
      }
    }

    // Scrub request data/body
    if (event.request?.data && typeof event.request.data === "object") {
      event.request.data = scrubSensitiveData(event.request.data);
    }

    // Scrub extra context
    if (event.extra) {
      event.extra = scrubSensitiveData(event.extra);
    }

    // Mask user email
    if (event.user?.email) {
      const email = event.user.email as string;
      const parts = email.split("@");
      if (parts.length === 2 && parts[0].length > 2) {
        event.user.email = `${parts[0].slice(0, 2)}***@${parts[1]}`;
      } else {
        event.user.email = "***@***.***";
      }
    }

    return event;
  },
});

/**
 * Recursively scrub sensitive data from objects.
 */
function scrubSensitiveData(obj: unknown): unknown {
  if (typeof obj !== "object" || obj === null) {
    return obj;
  }

  if (Array.isArray(obj)) {
    return obj.map((item) => scrubSensitiveData(item));
  }

  const scrubbed: Record<string, unknown> = {};
  const sensitiveKeys = [
    "password",
    "passwd",
    "secret",
    "token",
    "api_key",
    "apikey",
    "authorization",
    "cookie",
    "credit_card",
    "ssn",
    "social_security",
    "mekong_admin_token",
    "access_token",
    "refresh_token",
    "stripe_secret_key",
    "supabase_service_key",
    "polar_webhook_secret",
    "jwt_secret",
    "database_url",
    "db_password",
  ];

  for (const [key, value] of Object.entries(obj) as Array<[string, unknown]>) {
    const keyLower = key.toLowerCase();
    if (sensitiveKeys.some((sensitive) => keyLower.includes(sensitive))) {
      scrubbed[key] = "[Filtered]";
    } else if (typeof value === "object" && value !== null) {
      scrubbed[key] = scrubSensitiveData(value);
    } else {
      scrubbed[key] = value;
    }
  }

  return scrubbed;
}
