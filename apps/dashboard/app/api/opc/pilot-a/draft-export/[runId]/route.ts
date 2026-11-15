import {
  authorizeBffTenantRequest,
  buildBffJsonResponse,
  forwardToPilotAGateway,
  isValidRunId,
} from '@/lib/opc-bff-auth'

export const dynamic = 'force-dynamic'

const ALLOWED_FORMATS = new Set(['json', 'csv', 'xml'])
const ALLOWED_VAT_RATES = new Set(['0', '5', '8', '10'])
const ALLOWED_PROVIDERS = new Set(['misa_meinvoice', 'sapo_invoice'])

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

  const fmt = (url.searchParams.get('fmt') || 'json').trim().toLowerCase()
  if (!ALLOWED_FORMATS.has(fmt)) {
    return buildBffJsonResponse(
      { error: 'invalid_export_format', message: 'fmt must be json, csv, or xml.' },
      400
    )
  }

  const vatRatePct = (url.searchParams.get('vat_rate_pct') || '8').trim()
  if (!ALLOWED_VAT_RATES.has(vatRatePct)) {
    return buildBffJsonResponse(
      { error: 'invalid_vat_rate', message: 'vat_rate_pct must be 0, 5, 8, or 10.' },
      400
    )
  }

  const targetProvider = (url.searchParams.get('target_provider') || 'misa_meinvoice').trim()
  if (!ALLOWED_PROVIDERS.has(targetProvider)) {
    return buildBffJsonResponse(
      {
        error: 'invalid_target_provider',
        message: 'target_provider must be misa_meinvoice or sapo_invoice.',
      },
      400
    )
  }

  return forwardToPilotAGateway({
    path: `/v1/opc/pilot-a/draft-export/${encodeURIComponent(trimmedRunId)}`,
    method: 'GET',
    tenantId: auth.tenantId,
    tenantApiKey: auth.tenantApiKey,
    query: {
      fmt,
      vat_rate_pct: vatRatePct,
      target_provider: targetProvider,
      tenant_id: auth.tenantId,
    },
    expectText: true,
  })
}
