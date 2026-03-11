/**
 * OAuth Provider Configuration
 *
 * Better-Auth handles providers internally via socialProviders config.
 * This file documents the setup requirements for each provider.
 */

/**
 * Google OAuth Setup
 *
 * 1. Go to https://console.cloud.google.com/
 * 2. Create new project or select existing
 * 3. Enable Google+ API
 * 4. Create OAuth 2.0 credentials
 * 5. Add authorized redirect URI: http://localhost:3000/api/auth/callback/google
 * 6. Copy Client ID and Client Secret to .env
 */
export const googleOAuthConfig = {
  enabled: true,
  // Configured in src/lib/auth/config.ts via socialProviders.google
};

/**
 * GitHub OAuth Setup
 *
 * 1. Go to https://github.com/settings/developers
 * 2. Create new OAuth App
 * 3. Set Authorization callback URL: http://localhost:3000/api/auth/callback/github
 * 4. Copy Client ID and Client Secret to .env
 */
export const githubOAuthConfig = {
  enabled: true,
  // Configured in src/lib/auth/config.ts via socialProviders.github
};

/**
 * Environment variables required:
 * - GOOGLE_CLIENT_ID
 * - GOOGLE_CLIENT_SECRET
 * - GITHUB_CLIENT_ID
 * - GITHUB_CLIENT_SECRET
 */
