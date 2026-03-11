/**
 * RaaS API client for dashboard — typed fetch wrappers for all backend endpoints.
 * Base URL resolves from NEXT_PUBLIC_API_URL env or defaults to localhost:8000.
 */

const BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

export type MissionStatus = 'queued' | 'running' | 'completed' | 'failed' | 'cancelled';
export type MissionComplexity = 'simple' | 'standard' | 'complex';

export interface Mission {
  id: string;
  status: MissionStatus;
  goal: string;
  complexity: MissionComplexity;
  credits_cost: number;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  error_message: string | null;
  logs_url: string | null;
}

export interface CreditBalance {
  tenant_id: string;
  balance: number;
}

export interface CreditTransaction {
  id: string;
  amount: number;
  reason: string;
  timestamp: string;
}

export interface DailyUsage {
  date: string;
  credits_used: number;
  missions_count: number;
  missions_completed: number;
  missions_failed: number;
}

export interface UsageSummary {
  tenant_id: string;
  period_start: string;
  period_end: string;
  total_credits_used: number;
  total_missions: number;
  missions_completed: number;
  missions_failed: number;
  complexity_breakdown: Record<string, number>;
  daily_breakdown: DailyUsage[];
}

export interface ActivityItem {
  id: string;
  goal: string;
  status: MissionStatus;
  complexity: MissionComplexity;
  credits_cost: number;
  created_at: string;
  completed_at: string | null;
}

async function apiFetch<T>(path: string, token: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
      ...(init?.headers ?? {}),
    },
  });
  if (!res.ok) {
    const body = await res.text().catch(() => '');
    throw new Error(`API ${res.status}: ${body}`);
  }
  return res.json() as Promise<T>;
}

export const raasApi = {
  /** Submit a new mission */
  submitMission: (token: string, goal: string, complexity?: MissionComplexity) =>
    apiFetch<Mission>('/raas/missions', token, {
      method: 'POST',
      body: JSON.stringify({ goal, complexity }),
    }),

  /** List missions (paginated) */
  listMissions: (token: string, limit = 20, offset = 0) =>
    apiFetch<Mission[]>(`/raas/missions?limit=${limit}&offset=${offset}`, token),

  /** Get single mission */
  getMission: (token: string, id: string) =>
    apiFetch<Mission>(`/raas/missions/${id}`, token),

  /** Get credit balance */
  getBalance: (token: string) =>
    apiFetch<CreditBalance>('/raas/credits/balance', token),

  /** Get transaction history */
  getCreditHistory: (token: string, limit = 50) =>
    apiFetch<{ tenant_id: string; transactions: CreditTransaction[] }>(
      `/raas/credits/history?limit=${limit}`,
      token,
    ),

  /** Get usage summary */
  getUsageSummary: (token: string, days = 30) =>
    apiFetch<UsageSummary>(`/raas/usage/summary?days=${days}`, token),

  /** Get recent activity feed */
  getActivity: (token: string, limit = 10) =>
    apiFetch<{ tenant_id: string; activity: ActivityItem[] }>(
      `/raas/usage/activity?limit=${limit}`,
      token,
    ),
};
