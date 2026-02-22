import { describe, it, expect } from "vitest";
import { createPaymentWebhookRoutes } from "../../routes/payment-webhook";

// Helper to call the Hono router directly
async function callRoute(
    router: ReturnType<typeof createPaymentWebhookRoutes>,
    options: {
        method?: string;
        path?: string;
        body?: string;
        headers?: Record<string, string>;
    }
) {
    const method = options.method || "POST";
    const path = options.path || "/polar";
    const url = `http://localhost${path}`;

    const req = new Request(url, {
        method,
        body: options.body,
        headers: {
            "Content-Type": "application/json",
            ...options.headers,
        },
    });

    return router.fetch(req);
}

describe("Payment Webhook Route — POST /polar", () => {
    it("returns 400 when body is not valid JSON", async () => {
        const router = createPaymentWebhookRoutes();
        const res = await callRoute(router, { body: "not-json" });
        expect(res.status).toBe(400);
        const json = await res.json() as { success: boolean; error: { code: string } };
        expect(json.success).toBe(false);
        expect(json.error.code).toBe("BAD_REQUEST");
    });

    it("returns 400 when event type is missing", async () => {
        const router = createPaymentWebhookRoutes();
        const res = await callRoute(router, {
            body: JSON.stringify({ data: {} }),
        });
        expect(res.status).toBe(400);
        const json = await res.json() as { success: boolean; error: { code: string } };
        expect(json.success).toBe(false);
        expect(json.error.code).toBe("VALIDATION_ERROR");
    });

    it("acknowledges unknown event types gracefully", async () => {
        const router = createPaymentWebhookRoutes();
        const res = await callRoute(router, {
            body: JSON.stringify({ type: "unknown.event", data: {} }),
        });
        expect(res.status).toBe(200);
        const json = await res.json() as { received: boolean; event: string };
        expect(json.received).toBe(true);
        expect(json.event).toBe("unknown.event");
    });

    it("handles order.created event", async () => {
        const router = createPaymentWebhookRoutes();
        const res = await callRoute(router, {
            body: JSON.stringify({
                type: "order.created",
                data: { orderId: "ord_123", customerId: "cust_456" },
            }),
        });
        expect(res.status).toBe(200);
        const json = await res.json() as { received: boolean; event: string };
        expect(json.received).toBe(true);
        expect(json.event).toBe("order.created");
    });

    it("handles subscription.created event", async () => {
        const router = createPaymentWebhookRoutes();
        const res = await callRoute(router, {
            body: JSON.stringify({
                type: "subscription.created",
                data: { subscriptionId: "sub_789" },
            }),
        });
        expect(res.status).toBe(200);
        const json = await res.json() as { received: boolean; event: string };
        expect(json.received).toBe(true);
        expect(json.event).toBe("subscription.created");
    });

    it("handles subscription.updated event", async () => {
        const router = createPaymentWebhookRoutes();
        const res = await callRoute(router, {
            body: JSON.stringify({
                type: "subscription.updated",
                data: { subscriptionId: "sub_789", plan: "COMMANDER" },
            }),
        });
        expect(res.status).toBe(200);
        const json = await res.json() as { received: boolean; event: string };
        expect(json.received).toBe(true);
        expect(json.event).toBe("subscription.updated");
    });

    it("handles subscription.canceled event", async () => {
        const router = createPaymentWebhookRoutes();
        const res = await callRoute(router, {
            body: JSON.stringify({ type: "subscription.canceled", data: {} }),
        });
        expect(res.status).toBe(200);
        const json = await res.json() as { received: boolean; event: string };
        expect(json.received).toBe(true);
        expect(json.event).toBe("subscription.canceled");
    });

    it("handles subscription.revoked event", async () => {
        const router = createPaymentWebhookRoutes();
        const res = await callRoute(router, {
            body: JSON.stringify({ type: "subscription.revoked", data: {} }),
        });
        expect(res.status).toBe(200);
        const json = await res.json() as { received: boolean; event: string };
        expect(json.received).toBe(true);
        expect(json.event).toBe("subscription.revoked");
    });

    it("returns 401 when POLAR_WEBHOOK_SECRET is set and signature is missing", async () => {
        const originalSecret = process.env.POLAR_WEBHOOK_SECRET;
        process.env.POLAR_WEBHOOK_SECRET = "test_secret_key_12345";

        const router = createPaymentWebhookRoutes();
        const res = await callRoute(router, {
            body: JSON.stringify({ type: "order.created", data: {} }),
            headers: {}, // no webhook-signature header
        });
        expect(res.status).toBe(401);
        const json = await res.json() as { success: boolean; error: { code: string } };
        expect(json.success).toBe(false);
        expect(json.error.code).toBe("UNAUTHORIZED");

        process.env.POLAR_WEBHOOK_SECRET = originalSecret || "";
    });

    it("accepts request when signature is present and secret is set", async () => {
        const originalSecret = process.env.POLAR_WEBHOOK_SECRET;
        process.env.POLAR_WEBHOOK_SECRET = "test_secret_key_12345";

        const router = createPaymentWebhookRoutes();
        const res = await callRoute(router, {
            body: JSON.stringify({ type: "order.created", data: {} }),
            headers: {
                "webhook-signature": "sha256=valid_signature_here",
            },
        });
        expect(res.status).toBe(200);

        process.env.POLAR_WEBHOOK_SECRET = originalSecret || "";
    });
});
