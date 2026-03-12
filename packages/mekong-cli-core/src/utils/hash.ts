import { createHash } from 'node:crypto';

/** Generate SHA-256 hash of content */
export function sha256(content: string): string {
  return createHash('sha256').update(content).digest('hex');
}

/** Generate short ID (first 8 chars of SHA-256) */
export function shortId(content: string): string {
  return sha256(content).slice(0, 8);
}

/** Generate unique ID with timestamp prefix */
export function generateId(prefix?: string): string {
  const timestamp = Date.now().toString(36);
  const random = Math.random().toString(36).slice(2, 8);
  return prefix ? `${prefix}_${timestamp}${random}` : `${timestamp}${random}`;
}
