/**
 * Pilot Invite-Code Gate — single-use partner invite issuance & atomic tenant creation.
 *
 * Rules:
 * - Stores only SHA-256 hashes of invite codes (`code_hash`).
 * - Caps total issued partner codes at `maxInvites` (default: 5).
 * - Consumes a code atomically with tenant creation and returns the API key once.
 */

import type { D1Database } from '@cloudflare/workers-types'
import { hashApiKey } from './tenant'
import { TenantSchema, type Tenant } from '../types/raas'

const PILOT_INITIAL_CREDITS = 10

export interface PilotInviteRecord {
  id: string
  code_hash: string
  partner_label: string | null
  status: 'active' | 'redeemed' | 'revoked'
  issued_by: string
  redeemed_by_tenant_id: string | null
  created_at: string
  redeemed_at: string | null
}

export class PilotInviteError extends Error {
  constructor(
    public readonly code: string,
    message: string,
    public readonly statusCode: 400 | 401 | 403 | 409 = 403,
  ) {
    super(message)
    this.name = 'PilotInviteError'
  }
}

export async function hashInviteCode(rawCode: string): Promise<string> {
  const normalized = rawCode.trim()
  const data = new TextEncoder().encode(normalized)
  const hashBuffer = await crypto.subtle.digest('SHA-256', data)
  return Array.from(new Uint8Array(hashBuffer))
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('')
}

function generateRawInviteCode(): string {
  const bytes = new Uint8Array(16)
  crypto.getRandomValues(bytes)
  const hex = Array.from(bytes)
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('')
  return `mk_inv_${hex}`
}

export async function ensurePilotInviteTable(db: D1Database): Promise<void> {
  await db
    .exec(
      `CREATE TABLE IF NOT EXISTS pilot_invites (id TEXT PRIMARY KEY, code_hash TEXT NOT NULL UNIQUE, partner_label TEXT, status TEXT NOT NULL DEFAULT 'active', issued_by TEXT NOT NULL DEFAULT 'operator', redeemed_by_tenant_id TEXT, created_at TEXT NOT NULL DEFAULT (datetime('now')), redeemed_at TEXT)`,
    )
    .catch(() => {})
}

export function isPilotModeEnabled(envPilotMode?: string): boolean {
  if (!envPilotMode) return true
  return envPilotMode.toLowerCase() !== 'false' && envPilotMode !== '0'
}

export async function issuePilotInviteCode(
  db: D1Database,
  opts: { partnerLabel?: string; maxInvites?: number; issuedBy?: string } = {},
): Promise<{ invite: PilotInviteRecord; inviteCode: string }> {
  await ensurePilotInviteTable(db)
  const maxInvites = opts.maxInvites ?? 5

  const countRow = await db
    .prepare("SELECT COUNT(*) as total FROM pilot_invites WHERE status IN ('active', 'redeemed')")
    .first<{ total: number }>()
  const currentCount = countRow?.total ?? 0

  if (currentCount >= maxInvites) {
    throw new PilotInviteError(
      'PILOT_INVITE_LIMIT_REACHED',
      `Pilot invite limit of ${maxInvites} partner codes reached`,
      409,
    )
  }

  const inviteId = crypto.randomUUID()
  const inviteCode = generateRawInviteCode()
  const codeHash = await hashInviteCode(inviteCode)
  const now = new Date().toISOString()
  const partnerLabel = opts.partnerLabel?.trim() || null
  const issuedBy = opts.issuedBy ?? 'operator'

  await db
    .prepare(
      'INSERT INTO pilot_invites (id, code_hash, partner_label, status, issued_by, created_at) VALUES (?, ?, ?, ?, ?, ?)',
    )
    .bind(inviteId, codeHash, partnerLabel, 'active', issuedBy, now)
    .run()

  const invite: PilotInviteRecord = {
    id: inviteId,
    code_hash: codeHash,
    partner_label: partnerLabel,
    status: 'active',
    issued_by: issuedBy,
    redeemed_by_tenant_id: null,
    created_at: now,
    redeemed_at: null,
  }

  return { invite, inviteCode }
}

export async function listPilotInvites(db: D1Database): Promise<PilotInviteRecord[]> {
  await ensurePilotInviteTable(db)
  const res = await db
    .prepare(
      'SELECT id, code_hash, partner_label, status, issued_by, redeemed_by_tenant_id, created_at, redeemed_at FROM pilot_invites ORDER BY created_at ASC',
    )
    .all<PilotInviteRecord>()
  return res.results ?? []
}

export async function redeemInviteAndCreateTenant(
  db: D1Database,
  inviteCode: string | undefined,
  tenantName: string,
): Promise<{ tenant: Tenant; apiKey: string; inviteId: string; initialCredits: number }> {
  if (!inviteCode || !inviteCode.trim()) {
    throw new PilotInviteError(
      'INVITE_CODE_REQUIRED',
      'Pilot access is invite-only. A valid single-use invite_code is required.',
      403,
    )
  }

  await ensurePilotInviteTable(db)
  const codeHash = await hashInviteCode(inviteCode)
  const existing = await db
    .prepare('SELECT * FROM pilot_invites WHERE code_hash = ?')
    .bind(codeHash)
    .first<PilotInviteRecord>()

  if (!existing) {
    throw new PilotInviteError('INVALID_INVITE_CODE', 'Invalid invite code', 403)
  }

  if (existing.status !== 'active') {
    throw new PilotInviteError(
      'INVITE_CODE_ALREADY_USED',
      'Invite code has already been redeemed or revoked',
      409,
    )
  }

  const now = new Date().toISOString()
  const tenantId = crypto.randomUUID()
  const apiKey = `mk_${crypto.randomUUID().replace(/-/g, '')}`
  const apiKeyHash = await hashApiKey(apiKey)

  const consumeStmt = db
    .prepare(
      "UPDATE pilot_invites SET status = 'redeemed', redeemed_by_tenant_id = ?, redeemed_at = ? WHERE id = ? AND status = 'active'",
    )
    .bind(tenantId, now, existing.id)
  const insertTenantStmt = db
    .prepare('INSERT INTO tenants (id, name, api_key_hash, tier, created_at) VALUES (?, ?, ?, ?, ?)')
    .bind(tenantId, tenantName, apiKeyHash, 'free', now)
  const insertCreditsStmt = db
    .prepare('INSERT INTO credits (tenant_id, amount, reason) VALUES (?, ?, ?)')
    .bind(tenantId, PILOT_INITIAL_CREDITS, 'welcome: free tier pilot bonus')

  const [consumeResult] = typeof db.batch === 'function'
    ? await db.batch([consumeStmt, insertTenantStmt, insertCreditsStmt])
    : [await consumeStmt.run(), await insertTenantStmt.run(), await insertCreditsStmt.run()]

  const changes = (consumeResult as { meta?: { changes?: number } })?.meta?.changes ?? 0
  if (changes === 0) {
    throw new PilotInviteError('INVITE_CODE_ALREADY_USED', 'Invite code was concurrently redeemed', 409)
  }

  const tenant = TenantSchema.parse({ id: tenantId, name: tenantName, api_key_hash: apiKeyHash, tier: 'free', created_at: now })
  return { tenant, apiKey, inviteId: existing.id, initialCredits: PILOT_INITIAL_CREDITS }
}
