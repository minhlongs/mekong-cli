import { createHash, createHmac, randomBytes, timingSafeEqual } from 'node:crypto'

export const OPC_BFF_SESSION_COOKIE = 'mk_opc_session'
export const OPC_BFF_COOKIE_PATH = '/api/opc/pilot-a'

const SESSION_TOKEN_VERSION = 'v1'
const MIN_SESSION_SECRET_BYTES = 32
const MIN_LOGIN_TOKEN_BYTES = 16
const DEFAULT_SESSION_TTL_SECONDS = 8 * 3600
const GATEWAY_TIMEOUT_MS = 8000

const SLUG_REGEX = /^[a-zA-Z0-9][a-zA-Z0-9_-]{1,62}$/
const RUN_ID_REGEX = /^[a-zA-Z0-9][a-zA-Z0-9_-]{1,127}$/
const BASE64URL_SEGMENT_REGEX = /^[A-Za-z0-9_-]+$/
const HEX_SHA256_REGEX = /^[0-9a-fA-F]{64}$/
const RAW_TENANT_KEY_PATTERN = /mk_opc_[A-Za-z0-9_-]+/g

export type OpcBffRole = 'owner' | 'operator' | 'viewer'

export interface OpcBffSession {
  sub: string
  workspaceId: string
  allowedTenants: string[]
  role: OpcBffRole
  iat: number
  exp: number
}

export interface BffAuthFailure {
  ok: false
  status: 400 | 401 | 403 | 502 | 503
  error: string
  message: string
}

export interface BffAuthSuccess {
  ok: true
  session: OpcBffSession
  tenantId: string
  tenantApiKey: string
}

export type BffAuthResult = BffAuthSuccess | BffAuthFailure

const ROLE_RANK: Record<OpcBffRole, number> = {
  viewer: 1,
  operator: 2,
  owner: 3,
}

export function isPlainObject(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

export function isValidTenantSlug(value: unknown): value is string {
  return typeof value === 'string' && SLUG_REGEX.test(value)
}

export function isValidRunId(value: unknown): value is string {
  return typeof value === 'string' && RUN_ID_REGEX.test(value)
}

export function isValidOpcRole(value: unknown): value is OpcBffRole {
  return value === 'owner' || value === 'operator' || value === 'viewer'
}

function isProductionRuntime(): boolean {
  const nodeEnv = (process.env.NODE_ENV || '').trim().toLowerCase()
  const mekongEnv = (process.env.MEKONG_ENV || '').trim().toLowerCase()
  return nodeEnv === 'production' || mekongEnv === 'production'
}

function getSessionSecretResult(): { ok: true; secret: string } | BffAuthFailure {
  const rawSecret = (process.env.MEKONG_DASHBOARD_SESSION_SECRET || '').trim()
  if (
    rawSecret.length < MIN_SESSION_SECRET_BYTES ||
    Buffer.byteLength(rawSecret, 'utf8') < MIN_SESSION_SECRET_BYTES
  ) {
    return {
      ok: false,
      status: 503,
      error: 'bff_session_secret_unconfigured',
      message: 'Server session signing secret (MEKONG_DASHBOARD_SESSION_SECRET >= 32 chars) is not configured.',
    }
  }
  return { ok: true, secret: rawSecret }
}

export function constantTimeSecretEquals(left: string, right: string): boolean {
  if (!left || !right) {
    return false
  }
  const leftDigest = createHash('sha256').update(left, 'utf8').digest()
  const rightDigest = createHash('sha256').update(right, 'utf8').digest()
  return timingSafeEqual(leftDigest, rightDigest) && left.length === right.length
}

function signSessionSegment(secret: string, signingInput: string): Buffer {
  return createHmac('sha256', secret).update(signingInput, 'utf8').digest()
}

export function issueOpcBffSessionToken(
  claims: Omit<OpcBffSession, 'iat' | 'exp'>,
  ttlSeconds: number = DEFAULT_SESSION_TTL_SECONDS
): { ok: true; token: string; session: OpcBffSession } | BffAuthFailure {
  const secretRes = getSessionSecretResult()
  if (!secretRes.ok) {
    return secretRes
  }

  const trimmedSub = claims.sub.trim()
  if (!trimmedSub || trimmedSub.length > 128 || /[\r\n\0]/.test(trimmedSub)) {
    return {
      ok: false,
      status: 400,
      error: 'invalid_session_subject',
      message: 'Session subject (sub) must be a valid non-empty identifier.',
    }
  }

  if (!isValidTenantSlug(claims.workspaceId)) {
    return {
      ok: false,
      status: 400,
      error: 'invalid_workspace_id',
      message: 'Workspace ID must match tenant/workspace slug format.',
    }
  }

  if (
    !Array.isArray(claims.allowedTenants) ||
    claims.allowedTenants.length === 0 ||
    !claims.allowedTenants.every((slug) => isValidTenantSlug(slug))
  ) {
    return {
      ok: false,
      status: 400,
      error: 'invalid_allowed_tenants',
      message: 'Session must authorize at least one valid tenant slug.',
    }
  }

  if (!isValidOpcRole(claims.role)) {
    return {
      ok: false,
      status: 400,
      error: 'invalid_role',
      message: 'Session role must be owner, operator, or viewer.',
    }
  }

  const safeTtl = Math.max(60, Math.min(86400, Math.floor(ttlSeconds)))
  const nowSec = Math.floor(Date.now() / 1000)
  const deduplicatedTenants = Array.from(new Set(claims.allowedTenants))
  const session: OpcBffSession = {
    sub: trimmedSub,
    workspaceId: claims.workspaceId,
    allowedTenants: deduplicatedTenants,
    role: claims.role,
    iat: nowSec,
    exp: nowSec + safeTtl,
  }

  const payloadB64 = Buffer.from(JSON.stringify(session), 'utf8').toString('base64url')
  const signingInput = `${SESSION_TOKEN_VERSION}.${payloadB64}`
  const hmacHex = signSessionSegment(secretRes.secret, signingInput).toString('hex')
  return {
    ok: true,
    token: `${signingInput}.${hmacHex}`,
    session,
  }
}

export function verifyOpcBffSessionToken(
  token: string
): { ok: true; session: OpcBffSession } | BffAuthFailure {
  const secretRes = getSessionSecretResult()
  if (!secretRes.ok) {
    return secretRes
  }

  const trimmed = token.trim()
  if (!trimmed) {
    return {
      ok: false,
      status: 401,
      error: 'unauthenticated_bff_session',
      message: 'Missing BFF session token.',
    }
  }

  const parts = trimmed.split('.')
  if (parts.length !== 3 || parts[0] !== SESSION_TOKEN_VERSION) {
    return {
      ok: false,
      status: 401,
      error: 'unauthenticated_bff_session',
      message: 'Malformed BFF session token envelope.',
    }
  }

  const payloadB64 = parts[1]
  const presentedHex = parts[2]
  if (!BASE64URL_SEGMENT_REGEX.test(payloadB64) || !HEX_SHA256_REGEX.test(presentedHex)) {
    return {
      ok: false,
      status: 401,
      error: 'unauthenticated_bff_session',
      message: 'Invalid BFF session token encoding.',
    }
  }

  const signingInput = `${SESSION_TOKEN_VERSION}.${payloadB64}`
  const expectedMac = signSessionSegment(secretRes.secret, signingInput)
  const presentedMac = Buffer.from(presentedHex, 'hex')
  if (expectedMac.length !== presentedMac.length || !timingSafeEqual(expectedMac, presentedMac)) {
    return {
      ok: false,
      status: 401,
      error: 'unauthenticated_bff_session',
      message: 'Invalid BFF session HMAC signature.',
    }
  }

  let parsed: unknown
  try {
    const jsonText = Buffer.from(payloadB64, 'base64url').toString('utf8')
    parsed = JSON.parse(jsonText)
  } catch {
    return {
      ok: false,
      status: 401,
      error: 'unauthenticated_bff_session',
      message: 'Corrupted BFF session payload.',
    }
  }

  if (!isPlainObject(parsed)) {
    return {
      ok: false,
      status: 401,
      error: 'unauthenticated_bff_session',
      message: 'Invalid BFF session payload shape.',
    }
  }

  const { sub, workspaceId, allowedTenants, role, iat, exp } = parsed
  const nowSec = Math.floor(Date.now() / 1000)

  if (
    typeof sub !== 'string' ||
    sub.trim().length === 0 ||
    sub.length > 128 ||
    /[\r\n\0]/.test(sub) ||
    !isValidTenantSlug(workspaceId) ||
    !Array.isArray(allowedTenants) ||
    allowedTenants.length === 0 ||
    !allowedTenants.every((item): item is string => isValidTenantSlug(item)) ||
    !isValidOpcRole(role) ||
    typeof iat !== 'number' ||
    !Number.isInteger(iat) ||
    iat <= 0 ||
    typeof exp !== 'number' ||
    !Number.isInteger(exp) ||
    exp < iat ||
    exp <= nowSec
  ) {
    return {
      ok: false,
      status: 401,
      error: 'unauthenticated_bff_session',
      message: 'Expired or invalid BFF session claims.',
    }
  }

  return {
    ok: true,
    session: {
      sub: sub.trim(),
      workspaceId,
      allowedTenants: Array.from(new Set(allowedTenants)),
      role,
      iat,
      exp,
    },
  }
}

export function extractCookieValue(cookieHeader: string | null, cookieName: string): string | null {
  if (!cookieHeader) {
    return null
  }
  const segments = cookieHeader.split(';')
  for (const segment of segments) {
    const eqIndex = segment.indexOf('=')
    if (eqIndex === -1) continue
    const name = segment.slice(0, eqIndex).trim()
    if (name === cookieName) {
      const rawValue = segment.slice(eqIndex + 1).trim()
      try {
        return decodeURIComponent(rawValue)
      } catch {
        return rawValue
      }
    }
  }
  return null
}

export function verifyBffSessionFromRequest(
  request: Request
): { ok: true; session: OpcBffSession } | BffAuthFailure {
  const secretRes = getSessionSecretResult()
  if (!secretRes.ok) {
    return secretRes
  }
  const rawToken = extractCookieValue(request.headers.get('cookie'), OPC_BFF_SESSION_COOKIE)
  if (!rawToken) {
    return {
      ok: false,
      status: 401,
      error: 'unauthenticated_bff_session',
      message: 'Missing mk_opc_session cookie.',
    }
  }
  return verifyOpcBffSessionToken(rawToken)
}

function parseWorkspaceTenantsMap():
  | { ok: true; map: Record<string, string[]> | null }
  | BffAuthFailure {
  const raw = (process.env.MEKONG_WORKSPACE_TENANTS_JSON || '').trim()
  if (!raw) {
    return { ok: true, map: null }
  }
  let parsed: unknown
  try {
    parsed = JSON.parse(raw)
  } catch {
    return {
      ok: false,
      status: 503,
      error: 'invalid_workspace_tenants_config',
      message: 'Server MEKONG_WORKSPACE_TENANTS_JSON is not valid JSON.',
    }
  }
  if (!isPlainObject(parsed)) {
    return {
      ok: false,
      status: 503,
      error: 'invalid_workspace_tenants_config',
      message: 'Server MEKONG_WORKSPACE_TENANTS_JSON must be a JSON object mapping workspaceId to tenant arrays.',
    }
  }
  const normalized: Record<string, string[]> = {}
  for (const [wsId, tenants] of Object.entries(parsed)) {
    if (
      !isValidTenantSlug(wsId) ||
      !Array.isArray(tenants) ||
      !tenants.every((t): t is string => isValidTenantSlug(t))
    ) {
      return {
        ok: false,
        status: 503,
        error: 'invalid_workspace_tenants_config',
        message: 'Invalid workspace or tenant slug inside MEKONG_WORKSPACE_TENANTS_JSON.',
      }
    }
    normalized[wsId] = tenants
  }
  if (Object.keys(normalized).length === 0) {
    return { ok: true, map: null }
  }
  return { ok: true, map: normalized }
}

function parseServerTenantKeysMap():
  | { ok: true; map: Record<string, string> }
  | BffAuthFailure {
  const result: Record<string, string> = {}
  const rawJson = (process.env.MEKONG_TENANT_KEYS_JSON || '').trim()
  if (rawJson) {
    let parsed: unknown
    try {
      parsed = JSON.parse(rawJson)
    } catch {
      return {
        ok: false,
        status: 503,
        error: 'invalid_tenant_keys_config',
        message: 'Server MEKONG_TENANT_KEYS_JSON is not valid JSON.',
      }
    }
    if (!isPlainObject(parsed)) {
      return {
        ok: false,
        status: 503,
        error: 'invalid_tenant_keys_config',
        message: 'Server MEKONG_TENANT_KEYS_JSON must be a JSON object mapping tenantId to server API key.',
      }
    }
    for (const [tenantSlug, rawKey] of Object.entries(parsed)) {
      if (!isValidTenantSlug(tenantSlug) || typeof rawKey !== 'string' || !rawKey.trim()) {
        return {
          ok: false,
          status: 503,
          error: 'invalid_tenant_keys_config',
          message: 'Invalid tenant slug or empty API key in MEKONG_TENANT_KEYS_JSON.',
        }
      }
      result[tenantSlug] = rawKey.trim()
    }
  }

  const singleTenantId = (process.env.MEKONG_TENANT_ID || '').trim()
  const singleTenantKey = (process.env.MEKONG_TENANT_API_KEY || '').trim()
  if (singleTenantId && singleTenantKey && isValidTenantSlug(singleTenantId) && !result[singleTenantId]) {
    result[singleTenantId] = singleTenantKey
  }

  return { ok: true, map: result }
}

export function resolveServerTenantApiKey(
  requestedTenantId: string
): { ok: true; apiKey: string } | BffAuthFailure {
  const keysRes = parseServerTenantKeysMap()
  if (!keysRes.ok) {
    return keysRes
  }
  const resolved = keysRes.map[requestedTenantId]
  if (!resolved) {
    return {
      ok: false,
      status: 503,
      error: 'tenant_gateway_credentials_unconfigured',
      message: `No server-side gateway credential configured for tenant '${requestedTenantId}'.`,
    }
  }
  return { ok: true, apiKey: resolved }
}

export function authorizeBffTenantRequest(
  request: Request,
  requestedTenantId: unknown,
  requiredRole: OpcBffRole
): BffAuthResult {
  const sessionRes = verifyBffSessionFromRequest(request)
  if (!sessionRes.ok) {
    return sessionRes
  }

  const normalizedTenant =
    typeof requestedTenantId === 'string' ? requestedTenantId.trim() : requestedTenantId
  if (!isValidTenantSlug(normalizedTenant)) {
    return {
      ok: false,
      status: 400,
      error: 'invalid_tenant_id',
      message: 'Valid tenant_id slug is required.',
    }
  }

  const { session } = sessionRes
  if (!session.allowedTenants.includes(normalizedTenant)) {
    return {
      ok: false,
      status: 403,
      error: 'cross_tenant_forbidden',
      message: `Workspace '${session.workspaceId}' is not authorized to access tenant '${normalizedTenant}'.`,
    }
  }

  const wsMapRes = parseWorkspaceTenantsMap()
  if (!wsMapRes.ok) {
    return wsMapRes
  }
  if (wsMapRes.map !== null) {
    const mappedTenants = wsMapRes.map[session.workspaceId]
    if (!mappedTenants || !mappedTenants.includes(normalizedTenant)) {
      return {
        ok: false,
        status: 403,
        error: 'cross_tenant_forbidden',
        message: `Server workspace policy forbids '${session.workspaceId}' from accessing tenant '${normalizedTenant}'.`,
      }
    }
  }

  if (ROLE_RANK[session.role] < ROLE_RANK[requiredRole]) {
    return {
      ok: false,
      status: 403,
      error: 'insufficient_role',
      message: `Role '${session.role}' does not meet required role '${requiredRole}'.`,
    }
  }

  const keyRes = resolveServerTenantApiKey(normalizedTenant)
  if (!keyRes.ok) {
    return keyRes
  }

  return {
    ok: true,
    session,
    tenantId: normalizedTenant,
    tenantApiKey: keyRes.apiKey,
  }
}

export function verifySameOriginMutation(request: Request): BffAuthFailure | null {
  const secFetchSite = (request.headers.get('sec-fetch-site') || '').trim().toLowerCase()
  if (secFetchSite && secFetchSite !== 'same-origin' && secFetchSite !== 'none') {
    return {
      ok: false,
      status: 403,
      error: 'csrf_origin_mismatch',
      message: 'Cross-site request blocked by Sec-Fetch-Site policy.',
    }
  }

  const originHeader = request.headers.get('origin')
  if (originHeader !== null) {
    const trimmedOrigin = originHeader.trim()
    if (!trimmedOrigin || trimmedOrigin.toLowerCase() === 'null') {
      return {
        ok: false,
        status: 403,
        error: 'csrf_origin_mismatch',
        message: 'Null or empty Origin header is forbidden on mutating BFF routes.',
      }
    }

    let parsedOrigin: URL
    let parsedTarget: URL
    try {
      parsedOrigin = new URL(trimmedOrigin)
      parsedTarget = new URL(request.url)
    } catch {
      return {
        ok: false,
        status: 403,
        error: 'csrf_origin_mismatch',
        message: 'Malformed Origin header on mutating BFF route.',
      }
    }

    const forwardedHost = (request.headers.get('x-forwarded-host') || '').split(',')[0].trim()
    const hostHeader = (request.headers.get('host') || '').trim()
    const expectedHost = forwardedHost || hostHeader || parsedTarget.host
    const forwardedProto = (request.headers.get('x-forwarded-proto') || '').split(',')[0].trim()
    const expectedProto = forwardedProto ? `${forwardedProto.replace(/:$/, '')}:` : parsedTarget.protocol

    if (parsedOrigin.host !== expectedHost || parsedOrigin.protocol !== expectedProto) {
      return {
        ok: false,
        status: 403,
        error: 'csrf_origin_mismatch',
        message: 'Request Origin does not match BFF host origin.',
      }
    }
  }

  return null
}

export function buildSessionSetCookieHeader(token: string, maxAgeSeconds: number): string {
  const parts = [
    `${OPC_BFF_SESSION_COOKIE}=${encodeURIComponent(token)}`,
    'HttpOnly',
    'SameSite=Strict',
    `Path=${OPC_BFF_COOKIE_PATH}`,
    `Max-Age=${Math.max(0, Math.floor(maxAgeSeconds))}`,
  ]
  if (isProductionRuntime()) {
    parts.push('Secure')
  }
  return parts.join('; ')
}

export function buildClearedSessionCookieHeader(): string {
  return buildSessionSetCookieHeader('', 0)
}

export function authenticateBffOwnerLogin(params: {
  credential: string
  workspaceId?: string
  requestedTenants?: string[]
  role?: OpcBffRole
  sub?: string
}):
  | { ok: true; token: string; cookieHeader: string; session: OpcBffSession }
  | BffAuthFailure {
  const secretRes = getSessionSecretResult()
  if (!secretRes.ok) {
    return secretRes
  }

  const presented = params.credential.trim()
  if (!presented) {
    return {
      ok: false,
      status: 401,
      error: 'invalid_login_credential',
      message: 'Login credential is required.',
    }
  }

  const keysRes = parseServerTenantKeysMap()
  if (!keysRes.ok) {
    return keysRes
  }

  const wsMapRes = parseWorkspaceTenantsMap()
  if (!wsMapRes.ok) {
    return wsMapRes
  }

  const ownerBootstrapToken = (process.env.MEKONG_DASHBOARD_OWNER_LOGIN_TOKEN || '').trim()
  const hasOwnerBootstrap =
    ownerBootstrapToken.length >= MIN_LOGIN_TOKEN_BYTES &&
    Buffer.byteLength(ownerBootstrapToken, 'utf8') >= MIN_LOGIN_TOKEN_BYTES
  const configuredTenants = Object.keys(keysRes.map)

  if (!hasOwnerBootstrap && configuredTenants.length === 0) {
    return {
      ok: false,
      status: 503,
      error: 'bff_login_credentials_unconfigured',
      message: 'Neither MEKONG_DASHBOARD_OWNER_LOGIN_TOKEN (>= 16 chars) nor server tenant keys are configured.',
    }
  }

  const workspaceId = (params.workspaceId || 'ws_default').trim()
  if (!isValidTenantSlug(workspaceId)) {
    return {
      ok: false,
      status: 400,
      error: 'invalid_workspace_id',
      message: 'Valid workspace_id slug is required.',
    }
  }

  const requestedRole: OpcBffRole = params.role && isValidOpcRole(params.role) ? params.role : 'owner'
  const subjectId = (params.sub || '').trim() || `owner_${randomBytes(4).toString('hex')}`

  if (hasOwnerBootstrap && constantTimeSecretEquals(presented, ownerBootstrapToken)) {
    const workspaceAllowed =
      wsMapRes.map !== null
        ? wsMapRes.map[workspaceId] || []
        : configuredTenants.length > 0
        ? configuredTenants
        : ['default']

    const candidates =
      params.requestedTenants && params.requestedTenants.length > 0
        ? params.requestedTenants
        : workspaceAllowed

    if (candidates.length === 0 || !candidates.every((t) => isValidTenantSlug(t))) {
      return {
        ok: false,
        status: 400,
        error: 'invalid_tenant_id',
        message: 'At least one valid tenant_id slug is required.',
      }
    }

    if (wsMapRes.map !== null && !candidates.every((t) => workspaceAllowed.includes(t))) {
      return {
        ok: false,
        status: 403,
        error: 'cross_tenant_forbidden',
        message: `Workspace '${workspaceId}' is not authorized for the requested tenant(s).`,
      }
    }

    const issued = issueOpcBffSessionToken(
      {
        sub: subjectId,
        workspaceId,
        allowedTenants: candidates,
        role: requestedRole,
      },
      DEFAULT_SESSION_TTL_SECONDS
    )
    if (!issued.ok) {
      return issued
    }
    return {
      ok: true,
      token: issued.token,
      cookieHeader: buildSessionSetCookieHeader(issued.token, DEFAULT_SESSION_TTL_SECONDS),
      session: issued.session,
    }
  }

  // Check if presented credential matches a server-configured tenant key
  let matchedTenant: string | null = null
  for (const [tenantSlug, tenantSecret] of Object.entries(keysRes.map)) {
    if (constantTimeSecretEquals(presented, tenantSecret)) {
      matchedTenant = tenantSlug
    }
  }

  if (!matchedTenant) {
    return {
      ok: false,
      status: 401,
      error: 'invalid_login_credential',
      message: 'Invalid owner bootstrap token or server tenant credential.',
    }
  }

  if (params.requestedTenants && params.requestedTenants.length > 0) {
    if (params.requestedTenants.some((t) => t !== matchedTenant)) {
      return {
        ok: false,
        status: 403,
        error: 'cross_tenant_forbidden',
        message: 'Credential is scoped to a single tenant and cannot authorize other tenants.',
      }
    }
  }

  if (wsMapRes.map !== null) {
    const mapped = wsMapRes.map[workspaceId]
    if (!mapped || !mapped.includes(matchedTenant)) {
      return {
        ok: false,
        status: 403,
        error: 'cross_tenant_forbidden',
        message: `Workspace '${workspaceId}' is not mapped to tenant '${matchedTenant}'.`,
      }
    }
  }

  const issued = issueOpcBffSessionToken(
    {
      sub: subjectId,
      workspaceId,
      allowedTenants: [matchedTenant],
      role: requestedRole,
    },
    DEFAULT_SESSION_TTL_SECONDS
  )
  if (!issued.ok) {
    return issued
  }
  return {
    ok: true,
    token: issued.token,
    cookieHeader: buildSessionSetCookieHeader(issued.token, DEFAULT_SESSION_TTL_SECONDS),
    session: issued.session,
  }
}

export function scrubRawSecretsFromText(raw: string): string {
  return raw
    .replace(RAW_TENANT_KEY_PATTERN, '[REDACTED]')
    .replace(/([?&])sig=[0-9a-fA-F]{16,128}(&?)/g, (_match, prefix: string, trailingAmp: string) => {
      if (prefix === '?' && trailingAmp === '&') {
        return '?'
      }
      return trailingAmp ? prefix : ''
    })
}

export function sanitizeGatewayJsonPayload(value: unknown): unknown {
  if (typeof value === 'string') {
    return scrubRawSecretsFromText(value)
  }
  if (Array.isArray(value)) {
    return value.map((entry) => sanitizeGatewayJsonPayload(entry))
  }
  if (isPlainObject(value)) {
    const cleaned: Record<string, unknown> = {}
    for (const [key, entry] of Object.entries(value)) {
      if (key === 'card_sig' || key === 'api_key' || key === 'raw_api_key') {
        continue
      }
      cleaned[key] = sanitizeGatewayJsonPayload(entry)
    }
    return cleaned
  }
  return value
}

export function buildBffSecurityHeaders(extraHeaders?: Record<string, string>): Headers {
  const headers = new Headers({
    'Cache-Control': 'no-store, no-cache, must-revalidate',
    Pragma: 'no-cache',
    'Referrer-Policy': 'no-referrer',
    'X-Content-Type-Options': 'nosniff',
  })
  if (extraHeaders) {
    for (const [key, val] of Object.entries(extraHeaders)) {
      headers.set(key, val)
    }
  }
  return headers
}

export function buildBffJsonResponse(
  payload: unknown,
  status: number,
  extraHeaders?: Record<string, string>
): Response {
  const sanitized = sanitizeGatewayJsonPayload(payload)
  const headers = buildBffSecurityHeaders({
    'Content-Type': 'application/json; charset=utf-8',
    ...extraHeaders,
  })
  return new Response(JSON.stringify(sanitized), { status, headers })
}

function resolveGatewayInternalBaseUrl(): { ok: true; baseUrl: string } | BffAuthFailure {
  const configured = (process.env.MEKONG_GATEWAY_INTERNAL_URL || 'http://127.0.0.1:8000').trim()
  let parsed: URL
  try {
    parsed = new URL(configured)
  } catch {
    return {
      ok: false,
      status: 503,
      error: 'invalid_gateway_internal_url',
      message: 'MEKONG_GATEWAY_INTERNAL_URL must be a valid HTTP/HTTPS URL.',
    }
  }
  if (parsed.protocol !== 'http:' && parsed.protocol !== 'https:') {
    return {
      ok: false,
      status: 503,
      error: 'invalid_gateway_internal_url',
      message: 'MEKONG_GATEWAY_INTERNAL_URL must use http: or https: protocol.',
    }
  }
  return { ok: true, baseUrl: parsed.toString().replace(/\/+$/, '') }
}

export async function forwardToPilotAGateway(options: {
  path: string
  method: 'GET' | 'POST'
  tenantId: string
  tenantApiKey: string
  query?: Record<string, string>
  body?: Record<string, unknown>
  expectText?: boolean
}): Promise<Response> {
  if (!options.path.startsWith('/v1/opc/pilot-a/')) {
    return buildBffJsonResponse(
      { error: 'invalid_upstream_path', message: 'Upstream path must target /v1/opc/pilot-a/.' },
      400
    )
  }

  const baseRes = resolveGatewayInternalBaseUrl()
  if (!baseRes.ok) {
    return buildBffJsonResponse({ error: baseRes.error, message: baseRes.message }, baseRes.status)
  }

  const targetUrl = new URL(`${baseRes.baseUrl}${options.path}`)
  if (options.query) {
    for (const [k, v] of Object.entries(options.query)) {
      if (k !== 'sig') {
        targetUrl.searchParams.set(k, v)
      }
    }
  }
  if (options.method === 'GET' || options.query) {
    targetUrl.searchParams.set('tenant_id', options.tenantId)
  }

  const upstreamHeaders: Record<string, string> = {
    'X-API-Key': options.tenantApiKey,
    Accept: options.expectText ? '*/*' : 'application/json',
  }

  let serializedBody: string | undefined
  if (options.method === 'POST') {
    upstreamHeaders['Content-Type'] = 'application/json'
    const enforcedBody: Record<string, unknown> = {
      ...(options.body || {}),
      tenant_id: options.tenantId,
    }
    delete enforcedBody.card_sig
    serializedBody = JSON.stringify(enforcedBody)
  }

  const controller = new globalThis.AbortController()
  const timer = setTimeout(() => controller.abort(), GATEWAY_TIMEOUT_MS)

  try {
    const upstreamResponse = await fetch(targetUrl.toString(), {
      method: options.method,
      headers: upstreamHeaders,
      body: serializedBody,
      signal: controller.signal,
      cache: 'no-store',
    })
    clearTimeout(timer)

    const rawText = await upstreamResponse.text()

    if (options.expectText && upstreamResponse.ok) {
      const contentType =
        upstreamResponse.headers.get('content-type') || 'text/plain; charset=utf-8'
      const headers = buildBffSecurityHeaders({ 'Content-Type': contentType })
      return new Response(scrubRawSecretsFromText(rawText), {
        status: upstreamResponse.status,
        headers,
      })
    }

    let parsedJson: unknown
    try {
      parsedJson = rawText ? JSON.parse(rawText) : {}
    } catch {
      parsedJson = {
        error: upstreamResponse.ok ? 'invalid_upstream_json' : 'gateway_upstream_error',
        detail: scrubRawSecretsFromText(rawText.slice(0, 500)),
      }
    }

    return buildBffJsonResponse(parsedJson, upstreamResponse.status)
  } catch {
    clearTimeout(timer)
    return buildBffJsonResponse(
      {
        error: 'gateway_upstream_unreachable',
        message: 'Pilot A FastAPI Gateway is unreachable or timed out (fail-closed).',
      },
      502
    )
  }
}
