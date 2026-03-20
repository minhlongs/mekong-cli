/**
 * API Client - Enhanced with Auth Support
 */

import { API } from './auth-service';

export async function apiFetch(path: string, opts?: RequestInit) {
  const token = getAuthToken();
  const res = await fetch(API + path, {
    ...opts,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: 'Bearer ' + token } : {}),
      ...opts?.headers,
    },
  });
  return res.json();
}

export function getAuthToken(): string | null {
  // Try Supabase token first
  const supabaseToken = localStorage.getItem('sb-access-token');
  if (supabaseToken) return supabaseToken;
  // Fallback to API key
  return localStorage.getItem('mk_api_key');
}

export function setApiKey(key: string): void {
  localStorage.setItem('mk_api_key', key);
}

export function clearApiKey(): void {
  localStorage.removeItem('mk_api_key');
  localStorage.removeItem('mk_biz_name');
  localStorage.removeItem('sb-access-token');
  localStorage.removeItem('sb-refresh-token');
}

export function getBizName(): string {
  return localStorage.getItem('mk_biz_name') || 'Doanh nghiệp của bạn';
}

export { API };
