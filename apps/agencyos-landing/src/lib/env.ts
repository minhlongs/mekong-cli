import { createEnv } from "@t3-oss/env-nextjs";
import { z } from "zod";

export const env = createEnv({
  server: {
    // Polar.sh
    POLAR_ACCESS_TOKEN: z.string().min(1),
    POLAR_WEBHOOK_SECRET: z.string().min(1),
    POLAR_ORGANIZATION_ID: z.string().min(1),

    // Analytics
    ANALYTICS_WRITE_KEY: z.string().optional(),

    // Database (if needed for webhooks)
    DATABASE_URL: z.string().url().optional(),
  },
  client: {
    NEXT_PUBLIC_POLAR_PRICE_STARTER: z.string().min(1),
    NEXT_PUBLIC_POLAR_PRICE_PRO: z.string().min(1),
    NEXT_PUBLIC_ANALYTICS_HOST: z.string().url().optional(),
  },
  runtimeEnv: {
    // Server
    POLAR_ACCESS_TOKEN: process.env.POLAR_ACCESS_TOKEN,
    POLAR_WEBHOOK_SECRET: process.env.POLAR_WEBHOOK_SECRET,
    POLAR_ORGANIZATION_ID: process.env.POLAR_ORGANIZATION_ID,
    ANALYTICS_WRITE_KEY: process.env.ANALYTICS_WRITE_KEY,
    DATABASE_URL: process.env.DATABASE_URL,

    // Client
    NEXT_PUBLIC_POLAR_PRICE_STARTER: process.env.NEXT_PUBLIC_POLAR_PRICE_STARTER,
    NEXT_PUBLIC_POLAR_PRICE_PRO: process.env.NEXT_PUBLIC_POLAR_PRICE_PRO,
    NEXT_PUBLIC_ANALYTICS_HOST: process.env.NEXT_PUBLIC_ANALYTICS_HOST,
  },
  skipValidation: true, // Allow missing env vars during build
});
