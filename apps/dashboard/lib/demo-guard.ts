import { NextResponse } from 'next/server'

export const PRODUCTION_ENGINE_API_URL = 'https://api.cashclaw.cc'
export const PRODUCTION_ENGINE_WS_URL = 'wss://api.cashclaw.cc'

export function isDashboardDemoMode(): boolean {
  return process.env.DASHBOARD_DEMO_ONLY !== 'false' && process.env.NEXT_PUBLIC_DEMO_MODE !== 'false'
}

export function resolveEngineApiUrl(): string {
  const configured =
    process.env.NEXT_PUBLIC_API_URL ||
    process.env.NEXT_PUBLIC_AGENTIC_API_URL ||
    process.env.MEKONG_API_URL

  if (configured && configured.trim().length > 0) {
    return configured.replace(/\/$/, '')
  }

  return PRODUCTION_ENGINE_API_URL
}

export function resolveEngineWsUrl(path: string): string {
  const cleanPath = path.startsWith('/') ? path : `/${path}`
  const configuredWs = process.env.NEXT_PUBLIC_WS_URL
  if (configuredWs && configuredWs.trim().length > 0) {
    return `${configuredWs.replace(/\/$/, '')}${cleanPath}`
  }

  const httpBase = resolveEngineApiUrl()
  const wsBase = httpBase.replace(/^http/, 'ws')
  return `${wsBase}${cleanPath}`
}

/**
 * Protects or disables dashboard API routes outside of authorized access or in demo-only mode.
 * - In pilot demo mode (`DASHBOARD_DEMO_ONLY !== 'false'`), mutating requests (POST, PUT, PATCH, DELETE)
 *   are rejected with 403 so no external side effects (payments, emails, DB writes) can occur.
 * - Outside demo mode, requires `Authorization: Bearer <DASHBOARD_API_TOKEN>`.
 */
export function guardDashboardApiRoute(
  request: Request,
  opts: { allowSyntheticGet?: boolean } = {},
): NextResponse | null {
  const method = request.method.toUpperCase()
  const demoOnly = isDashboardDemoMode()

  if (demoOnly) {
    if (method === 'GET' && opts.allowSyntheticGet) {
      return null
    }
    return NextResponse.json(
      {
        error: 'DEMO_MODE_PROTECTED_ROUTE',
        message: 'Dashboard API route is disabled in the synthetic pilot demo. No live mutations or partner data are exposed.',
        synthetic: true,
      },
      { status: 403 },
    )
  }

  const expectedToken = process.env.DASHBOARD_API_TOKEN
  const authHeader = request.headers.get('authorization') || ''
  if (!expectedToken || authHeader !== `Bearer ${expectedToken}`) {
    return NextResponse.json(
      {
        error: 'UNAUTHORIZED_DASHBOARD_API',
        message: 'Dashboard API route requires valid operator authorization.',
      },
      { status: 401 },
    )
  }

  return null
}
