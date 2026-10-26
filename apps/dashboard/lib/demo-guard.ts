import { NextResponse } from 'next/server';

export function isDashboardDemoMode(): boolean {
  return process.env.NEXT_PUBLIC_DEMO_MODE !== 'false';
}

export function resolveEngineApiUrl(): string {
  return process.env.NEXT_PUBLIC_ENGINE_API_URL || 'http://localhost:8000';
}

export function guardDashboardApiRoute(
  _request: Request,
  options?: { allowSyntheticGet?: boolean }
): NextResponse | null {
  if (options?.allowSyntheticGet) {
    return null;
  }
  return null;
}
