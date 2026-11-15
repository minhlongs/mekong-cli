import {
  authenticateBffOwnerLogin,
  buildBffJsonResponse,
  buildClearedSessionCookieHeader,
  isPlainObject,
  isValidOpcRole,
  verifyBffSessionFromRequest,
  verifySameOriginMutation,
} from '@/lib/opc-bff-auth'

export const dynamic = 'force-dynamic'

export async function GET(request: Request): Promise<Response> {
  const verified = verifyBffSessionFromRequest(request)
  if (!verified.ok) {
    return buildBffJsonResponse(
      {
        authenticated: false,
        error: verified.error,
        message: verified.message,
      },
      verified.status
    )
  }

  const { session } = verified
  return buildBffJsonResponse(
    {
      authenticated: true,
      sub: session.sub,
      workspaceId: session.workspaceId,
      allowedTenants: session.allowedTenants,
      role: session.role,
      exp: session.exp,
    },
    200
  )
}

export async function POST(request: Request): Promise<Response> {
  const csrfError = verifySameOriginMutation(request)
  if (csrfError) {
    return buildBffJsonResponse(
      { authenticated: false, error: csrfError.error, message: csrfError.message },
      csrfError.status
    )
  }

  let parsedBody: unknown
  try {
    parsedBody = await request.json()
  } catch {
    return buildBffJsonResponse(
      { authenticated: false, error: 'invalid_json', message: 'Request body must be valid JSON.' },
      400
    )
  }

  if (!isPlainObject(parsedBody)) {
    return buildBffJsonResponse(
      { authenticated: false, error: 'invalid_request', message: 'Request body must be a JSON object.' },
      400
    )
  }

  const rawCredential =
    typeof parsedBody.credential === 'string'
      ? parsedBody.credential
      : typeof parsedBody.login_token === 'string'
      ? parsedBody.login_token
      : ''

  const workspaceId =
    typeof parsedBody.workspace_id === 'string'
      ? parsedBody.workspace_id
      : typeof parsedBody.workspaceId === 'string'
      ? parsedBody.workspaceId
      : undefined

  let requestedTenants: string[] | undefined
  if (Array.isArray(parsedBody.allowed_tenants)) {
    if (!parsedBody.allowed_tenants.every((item): item is string => typeof item === 'string')) {
      return buildBffJsonResponse(
        { authenticated: false, error: 'invalid_tenant_id', message: 'allowed_tenants must be an array of strings.' },
        400
      )
    }
    requestedTenants = parsedBody.allowed_tenants
  } else if (typeof parsedBody.tenant_id === 'string' && parsedBody.tenant_id.trim()) {
    requestedTenants = [parsedBody.tenant_id.trim()]
  }

  const roleValue = parsedBody.role
  if (roleValue !== undefined && !isValidOpcRole(roleValue)) {
    return buildBffJsonResponse(
      { authenticated: false, error: 'invalid_role', message: 'role must be owner, operator, or viewer.' },
      400
    )
  }

  const sub = typeof parsedBody.sub === 'string' ? parsedBody.sub : undefined

  const loginRes = authenticateBffOwnerLogin({
    credential: rawCredential,
    workspaceId,
    requestedTenants,
    role: roleValue,
    sub,
  })

  if (!loginRes.ok) {
    return buildBffJsonResponse(
      { authenticated: false, error: loginRes.error, message: loginRes.message },
      loginRes.status
    )
  }

  const { session, cookieHeader } = loginRes
  return buildBffJsonResponse(
    {
      authenticated: true,
      sub: session.sub,
      workspaceId: session.workspaceId,
      allowedTenants: session.allowedTenants,
      role: session.role,
      exp: session.exp,
    },
    200,
    { 'Set-Cookie': cookieHeader }
  )
}

export async function DELETE(request: Request): Promise<Response> {
  const csrfError = verifySameOriginMutation(request)
  if (csrfError) {
    return buildBffJsonResponse(
      { authenticated: false, error: csrfError.error, message: csrfError.message },
      csrfError.status
    )
  }

  return buildBffJsonResponse(
    { authenticated: false },
    200,
    { 'Set-Cookie': buildClearedSessionCookieHeader() }
  )
}
