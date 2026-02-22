import { Hono } from "hono";

const PLANS = [
    {
        id: "genesis",
        name: "GENESIS",
        price: 0,
        agents: 2,
        features: ["Basic ROI tracking", "Community support"],
    },
    {
        id: "commander",
        name: "COMMANDER",
        price: 99,
        agents: 12,
        features: ["Advanced AI agents", "Priority support", "Custom strategies"],
    },
    {
        id: "emperor",
        name: "EMPEROR",
        price: 499,
        agents: 100,
        features: [
            "Unlimited agents",
            "White-glove support",
            "Custom AI models",
            "Dedicated infrastructure",
        ],
    },
];

export function createSubscriptionRoutes() {
    const router = new Hono();

    // GET /api/subscriptions/plans
    router.get("/plans", (c) => {
        return c.json({ plans: PLANS });
    });

    return router;
}
