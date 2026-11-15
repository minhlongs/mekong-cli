import {
  authorizeBffTenantRequest,
  buildBffJsonResponse,
  forwardToPilotAGateway,
  isPlainObject,
  isValidRunId,
  verifySameOriginMutation,
} from '@/lib/opc-bff-auth'

export const dynamic = 'force-dynamic'

const ALLOWED_DECISIONS = new Set(['approve', 'reject', 'revise', 'handoff'])

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

  const normalizedDecision =
    typeof parsedBody.decision === 'string' ? parsedBody.decision.trim().toLowerCase() : ''

  // Operators may only trigger 'handoff'; approving, rejecting, or revising quotes requires 'owner'.
  const requiredRole = normalizedDecision === 'handoff' ? 'operator' : 'owner'
  const auth = authorizeBffTenantRequest(request, parsedBody.tenant_id, requiredRole)
  if (!auth.ok) {
    return buildBffJsonResponse({ error: auth.error, message: auth.message }, auth.status)
  }

  if (!ALLOWED_DECISIONS.has(normalizedDecision)) {
    return buildBffJsonResponse(
      { error: 'invalid_decision', message: 'decision must be approve, reject, revise, or handoff.' },
      400
    )
  }

  const runId = typeof parsedBody.run_id === 'string' ? parsedBody.run_id.trim() : ''
  if (!isValidRunId(runId)) {
    return buildBffJsonResponse(
      { error: 'invalid_run_id', message: 'Valid run_id is required.' },
      400
    )
  }

  const actionDigest =
    typeof parsedBody.action_digest === 'string' ? parsedBody.action_digest.trim() : ''
  if (actionDigest.length < 16 || actionDigest.length > 128) {
    return buildBffJsonResponse(
      { error: 'invalid_action_digest', message: 'Valid SHA-256 action_digest is required.' },
      400
    )
  }

  const revisionNotes =
    typeof parsedBody.revision_notes === 'string' ? parsedBody.revision_notes.slice(0, 1000) : ''

  const upstreamBody: Record<string, unknown> = {
    run_id: runId,
    tenant_id: auth.tenantId,
    decision: normalizedDecision,
    action_digest: actionDigest,
    revision_notes: revisionNotes,
  }

  if (typeof parsedBody.idempotency_key === 'string' && parsedBody.idempotency_key.trim()) {
    upstreamBody.idempotency_key = parsedBody.idempotency_key.trim().slice(0, 128)
  }

  return forwardToPilotAGateway({
    path: '/v1/opc/pilot-a/decide',
    method: 'POST',
    tenantId: auth.tenantId,
    tenantApiKey: auth.tenantApiKey,
    body: upstreamBody,
  })
}
