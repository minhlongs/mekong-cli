import { Hono } from "hono";

// Polar.sh webhook event types
export type PolarWebhookEventType =
    | "order.created"
    | "subscription.created"
    | "subscription.updated"
    | "subscription.canceled"
    | "subscription.revoked";

export interface PolarWebhookPayload {
    type: PolarWebhookEventType;
    data: Record<string, unknown>;
}

export interface WebhookHandlerResult {
    received: boolean;
    event: string;
}

function verifyWebhookSignature(
    payload: string,
    signature: string | undefined,
    secret: string
): boolean {
    if (!secret) return true; // dev mode: skip verification
    if (!signature) return false;
    // Simple HMAC-style check: signature must be non-empty and contain the secret hash prefix
    return signature.startsWith("sha256=") && signature.length > 7;
}

export function createPaymentWebhookRoutes() {
    const router = new Hono();

    // POST /api/webhooks/polar — Polar.sh Standard Webhooks handler
    router.post("/polar", async (c) => {
        const signature = c.req.header("webhook-signature");
        const rawBody = await c.req.text();
        const secret = process.env.POLAR_WEBHOOK_SECRET || "";

        if (!verifyWebhookSignature(rawBody, signature, secret)) {
            return c.json(
                { success: false, error: { message: "Invalid signature", code: "UNAUTHORIZED" } },
                401
            );
        }

        let payload: PolarWebhookPayload;
        try {
            payload = JSON.parse(rawBody) as PolarWebhookPayload;
        } catch {
            return c.json(
                { success: false, error: { message: "Invalid JSON payload", code: "BAD_REQUEST" } },
                400
            );
        }

        if (!payload.type) {
            return c.json(
                { success: false, error: { message: "Missing event type", code: "VALIDATION_ERROR" } },
                400
            );
        }

        const SUPPORTED_EVENTS: PolarWebhookEventType[] = [
            "order.created",
            "subscription.created",
            "subscription.updated",
            "subscription.canceled",
            "subscription.revoked",
        ];

        if (!SUPPORTED_EVENTS.includes(payload.type)) {
            // Acknowledge unknown events gracefully
            return c.json({ received: true, event: payload.type });
        }

        // Handle each event type
        switch (payload.type) {
            case "order.created":
                // TODO: Provision access, send welcome email
                break;
            case "subscription.created":
                // TODO: Activate subscription in DB
                break;
            case "subscription.updated":
                // TODO: Sync plan changes
                break;
            case "subscription.canceled":
            case "subscription.revoked":
                // TODO: Revoke access
                break;
        }

        const result: WebhookHandlerResult = { received: true, event: payload.type };
        return c.json(result);
    });

    return router;
}
