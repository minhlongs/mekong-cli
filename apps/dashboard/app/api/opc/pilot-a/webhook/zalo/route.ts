import {
  authorizeBffTenantRequest,
  buildBffJsonResponse,
  forwardToPilotAGateway,
  isPlainObject,
  verifySameOriginMutation,
} from '@/lib/opc-bff-auth'

export const dynamic = 'force-dynamic'

export async function POST(request: Request): Promise<Response> {
  const csrfError = verifySameOriginMutation(request)
  if (csrfError) {
    return buildBffJsonResponse(
      { error: csrfError.error, message: csrfError.message },
      csrfError.status
    )
  }

  let parsedBody: unknown
  try {
    parsedBody = await request.json()
  } catch {
    return buildBffJsonResponse(
      { error: 'invalid_json', message: 'Request body must be valid JSON.' },
      400
    )
  }

  if (!isPlainObject(parsedBody)) {
    return buildBffJsonResponse(
      { error: 'invalid_request', message: 'Request body must be a JSON object.' },
      400
    )
  }

  const auth = authorizeBffTenantRequest(request, parsedBody.tenant_id, 'operator')
  if (!auth.ok) {
    return buildBffJsonResponse({ error: auth.error, message: auth.message }, auth.status)
  }

  if (
    typeof parsedBody.event_id !== 'string' ||
    !parsedBody.event_id.trim() ||
    typeof parsedBody.sender_id !== 'string' ||
    !parsedBody.sender_id.trim() ||
    typeof parsedBody.sender_name !== 'string' ||
    !parsedBody.sender_name.trim() ||
    typeof parsedBody.message_text !== 'string' ||
    !parsedBody.message_text.trim()
  ) {
    return buildBffJsonResponse(
      {
        error: 'invalid_webhook_payload',
        message: 'event_id, sender_id, sender_name, and message_text are required.',
      },
      400
    )
  }

  const sanitizedBody: Record<string, unknown> = {
    ...parsedBody,
    tenant_id: auth.tenantId,
    grant_consent: false,
  }

  if (auth.session.role !== 'owner') {
    delete sanitizedBody.service_rates_vnd
  }
  delete sanitizedBody.card_sig

  return forwardToPilotAGateway({
    path: '/v1/opc/pilot-a/webhook/zalo',
    method: 'POST',
    tenantId: auth.tenantId,
    tenantApiKey: auth.tenantApiKey,
    body: sanitizedBody,
  })
}
