const API = 'https://mekong-engine.agencyos-openclaw.workers.dev';

export async function apiFetch(path: string, opts?: RequestInit) {
  const key = localStorage.getItem('mk_api_key');
  const res = await fetch(API + path, {
    ...opts,
    headers: {
      'Content-Type': 'application/json',
      ...(key ? { Authorization: 'Bearer ' + key } : {}),
      ...opts?.headers,
    },
  });
  return res.json();
}

export function getApiKey(): string | null {
  return localStorage.getItem('mk_api_key');
}

export function setApiKey(key: string): void {
  localStorage.setItem('mk_api_key', key);
}

export function clearApiKey(): void {
  localStorage.removeItem('mk_api_key');
  localStorage.removeItem('mk_biz_name');
}

export function getBizName(): string {
  return localStorage.getItem('mk_biz_name') || 'Doanh nghiệp của bạn';
}
