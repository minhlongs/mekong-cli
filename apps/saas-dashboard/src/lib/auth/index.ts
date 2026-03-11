export { auth } from './config';
export type { Auth } from './config';
export { googleOAuthConfig, githubOAuthConfig } from './providers';

/**
 * OAuth provider types
 */
export type OAuthProvider = 'google' | 'github';

/**
 * Helper types cho auth
 */
export interface UserSession {
  id: string;
  email: string;
  fullName?: string | null;
  role: 'admin' | 'user' | 'viewer';
  avatarUrl?: string | null;
}

export interface AuthTokens {
  accessToken: string;
  refreshToken?: string;
  expiresAt: number;
}
