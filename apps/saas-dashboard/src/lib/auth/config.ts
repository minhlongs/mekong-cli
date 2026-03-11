import { betterAuth } from 'better-auth';
import { nextCookies } from 'better-auth/next-js';

/**
 * Better-Auth Configuration
 *
 * Features:
 * - Email/Password authentication
 * - OAuth providers (Google, GitHub)
 * - Session management with cookies
 * - JWT tokens for API auth
 */
export const auth = betterAuth({
  database: {
    // Supabase PostgreSQL connection
    // Format: postgresql://[user]:[password]@[host]:[port]/[dbname]
    url: process.env.DATABASE_URL!,
  },

  emailAndPassword: {
    enabled: true,
    requireEmailVerification: false, // Set true trong production
    minPasswordLength: 8,
    maxPasswordLength: 128,
  },

  socialProviders: {
    google: {
      enabled: process.env.GOOGLE_CLIENT_ID ? true : false,
      clientId: process.env.GOOGLE_CLIENT_ID!,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
      scope: ['openid', 'email', 'profile'],
    },
    github: {
      enabled: process.env.GITHUB_CLIENT_ID ? true : false,
      clientId: process.env.GITHUB_CLIENT_ID!,
      clientSecret: process.env.GITHUB_CLIENT_SECRET!,
      scope: ['user:email'],
    },
  },

  plugins: [
    nextCookies(), // Tích hợp Next.js cookies
  ],

  session: {
    expiresIn: 60 * 60 * 24 * 7, // 7 days
    updateAge: 60 * 60 * 24, // 1 day (every 1 day session expires)
    cookieCache: {
      enabled: true,
      maxAge: 60 * 5, // 5 minutes
    },
  },

  user: {
    additionalFields: {
      fullName: {
        type: 'string',
        required: false,
      },
      role: {
        type: 'string',
        required: false,
        defaultValue: 'user',
      },
    },
  },
});

export type Auth = typeof auth;
