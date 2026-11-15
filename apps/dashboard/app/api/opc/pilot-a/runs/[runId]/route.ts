import {
  authorizeBffTenantRequest,
  buildBffJsonResponse,
  forwardToPilotAGateway,
  isValidRunId,
} from '@/lib/opc-bff-auth'

export const dynamic = 'force-dynamic'

export async function GET(
  request: Request,
  context: { params: Promise<{ runId: string }> }
): Promise<Response> {
  const { runId } = await context.params
  const url = new URL(request.url)
  const requestedTenantId = url.searchParams.get('tenant_id')

  const auth = authorizeBffTenantRequest(request, requestedTenantId, 'viewer')
  if (!auth.ok) {
    return buildBffJsonResponse({ error: auth.error, message: auth.message }, auth.status)
  }

  const trimmedRunId = typeof runId === 'string' ? runId.trim() : ''
  if (!isValidRunId(trimmedRunId)) {
    return buildBffJsonResponse(
      { error: 'invalid_run_id', message: 'Valid runId path parameter is required.' },
      400
    )
  }

  return forwardToPilotAGateway({
    path: `/v1/opc/pilot-a/runs/${encodeURIComponent(trimmedRunId)}`,
    method: 'GET',
    tenantId: auth.tenantId,
    tenantApiKey: auth.tenantApiKey,
    query: { tenant_id: auth.tenantId },
  })
}
