/**
 * Sentry Client Configuration
 *
 * This file is used to configure Sentry for the browser/React client.
 * It runs only on the client side and captures frontend errors.
 */
import * as Sentry from "@sentry/nextjs";

export const getClientSentryConfig = () => ({
  // Automatically capture unhandled errors and promise rejections
  autoSessionTracking: true,
  // Collect performance data for frontend
  tracesSampleRate: 1.0, // 100% in dev, lower in prod via env var
  // Capture console logs as breadcrumbs
  beforeBreadcrumb(breadcrumb) {
    // Filter out sensitive console logs
    if (breadcrumb.category === "console") {
      const message = breadcrumb.message || "";
      // Filter potentially sensitive patterns
      const sensitivePatterns = [
        /password/i,
        /token/i,
        /api[_-]?key/i,
        /secret/i,
        /authorization/i,
        /bearer/i,
      ];
      if (sensitivePatterns.some((re) => re.test(message))) {
        return null; // Drop this breadcrumb
      }
    }
    return breadcrumb;
  },
  // Before sending an event, scrub sensitive data
  beforeSend(event, hint) {
    // Remove sensitive data from event
    if (event.request) {
      // Remove authorization headers
      if (event.request.headers) {
        const sensitiveHeaders = ["authorization", "cookie", "x-api-key", "x-idempotency-key"];
        for (const header of sensitiveHeaders) {
          if (event.request.headers[header]) {
            event.request.headers[header] = "[Filtered]";
          }
        }
      }
      // Scrub request data/body
      if (event.request.data && typeof event.request.data === "object") {
        event.request.data = scrubSensitiveData(event.request.data);
      }
    }

    // Scrub extra context
    if (event.extra) {
      event.extra = scrubSensitiveData(event.extra);
    }

    // Mask user email if present
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
