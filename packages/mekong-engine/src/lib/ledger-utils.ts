/**
 * Ledger Utilities - Shared functions for double-entry accounting operations
 *
 * Provides account management, transfer operations, and balance checks
 * with proper error handling and edge case coverage.
 */

import type { D1Database, D1PreparedStatement } from '@cloudflare/workers-types'
import { HttpError, createError } from '../types/error'

/**
 * Ensure account exists (upsert pattern)
 * Creates account if not exists, returns account ID
 *
 * @param db - D1 database instance
 * @param tenantId - Tenant identifier
 * @param code - Account code (e.g., 'revenue:platform', 'asset:customer:123')
 * @param type - Account type (asset, liability, equity, revenue, expense)
 * @param ownerId - Optional owner reference (stakeholder ID)
 * @returns Account ID
 */
export async function ensureAccount(
  db: D1Database,
  tenantId: string,
  code: string,
  type: string,
  ownerId?: string
): Promise<string> {
  // Try to find existing account
  const existing = await db
    .prepare('SELECT id FROM ledger_accounts WHERE tenant_id = ? AND code = ?')
    .bind(tenantId, code)
    .first()

  if (existing) {
    return (existing as { id: string }).id
  }

  // Create new account
  const id = crypto.randomUUID()
  await db
    .prepare(
      'INSERT INTO ledger_accounts (id, tenant_id, owner_id, code, account_type) VALUES (?, ?, ?, ?, ?)'
    )
    .bind(id, tenantId, ownerId ?? null, code, type)
    .run()

  return id
}

/**
 * Get account balance with null-safety
 * Returns 0 if account doesn't exist
 *
 * @param db - D1 database instance
 * @param accountId - Account ID
 * @returns Current balance
 */
export async function getAccountBalance(
  db: D1Database,
  accountId: string
): Promise<number> {
  const result = await db
    .prepare('SELECT balance FROM ledger_accounts WHERE id = ?')
    .bind(accountId)
    .first()

  return (result as { balance: number } | null)?.balance ?? 0
}

/**
 * Check if account has sufficient balance
 * Throws INSUFFICIENT_CREDITS error if not
 *
 * @param db - D1 database instance
 * @param accountId - Account ID
 * @param amount - Amount to check
 * @param errorMessage - Custom error message
 * @throws HttpError with INSUFFICIENT_CREDITS code
 */
export async function requireBalance(
  db: D1Database,
  accountId: string,
  amount: number,
  errorMessage?: string
): Promise<void> {
  const balance = await getAccountBalance(db, accountId)

  if (balance < amount) {
    throw new HttpError(
      'INSUFFICIENT_CREDITS',
      errorMessage ?? `Insufficient balance. Required: ${amount}, Available: ${balance}`,
      [{ balance, required: amount }]
    )
  }
}

/**
 * Create a double-entry journal entry
 * Atomically records debit and credit lines
 *
 * @param db - D1 database instance
 * @param tenantId - Tenant identifier
 * @param description - Transaction description
 * @param entryType - Entry type (transfer, topup, revenue_share, etc.)
 * @param lines - Array of debit/credit lines
 * @param idempotencyKey - Optional idempotency key
 * @returns Journal entry ID
 */
export async function createJournalEntry(
  db: D1Database,
  tenantId: string,
  description: string,
  entryType: string,
  lines: Array<{
    accountId: string
    amount: number
    direction: number // 1 for credit, -1 for debit
  }>,
  idempotencyKey?: string
): Promise<string> {
  // Check idempotency
  if (idempotencyKey) {
    const existing = await db
      .prepare('SELECT id FROM journal_entries WHERE idempotency_key = ?')
      .bind(idempotencyKey)
      .first()

    if (existing) {
      return (existing as { id: string }).id
    }
  }

  const jeId = crypto.randomUUID()
  const batch: D1PreparedStatement[] = []

  // Insert journal entry
  batch.push(
    db
      .prepare(
        'INSERT INTO journal_entries (id, tenant_id, description, entry_type, idempotency_key) VALUES (?, ?, ?, ?, ?)'
      )
      .bind(jeId, tenantId, description, entryType, idempotencyKey ?? null)
  )

  // Insert transaction lines and update balances
  for (const line of lines) {
    const lineId = crypto.randomUUID()
    batch.push(
      db
        .prepare(
          'INSERT INTO transaction_lines (id, journal_entry_id, account_id, amount, direction) VALUES (?, ?, ?, ?, ?)'
        )
        .bind(lineId, jeId, line.accountId, line.amount, line.direction)
    )

    // Update account balance
    const balanceChange = line.direction * line.amount
    if (balanceChange !== 0) {
      batch.push(
        db
          .prepare('UPDATE ledger_accounts SET balance = balance + ? WHERE id = ?')
          .bind(balanceChange, line.accountId)
      )
    }
  }

  // Execute atomically
  await db.batch(batch)

  return jeId
}

/**
 * Validate that debits equal credits
 * Returns true if balanced, false otherwise
 *
 * @param lines - Array of transaction lines
 * @returns True if balanced
 */
export function validateDoubleEntry(lines: Array<{ amount: number; direction: number }>): boolean {
  const total = lines.reduce((sum, line) => sum + line.amount * line.direction, 0)
  return total === 0
}

/**
 * Get transaction history for an account
 * Supports pagination and date filtering
 *
 * @param db - D1 database instance
 * @param accountId - Account ID
 * @param limit - Max results (default: 50, max: 200)
 * @param offset - Pagination offset
 * @returns Transaction history
 */
export async function getTransactionHistory(
  db: D1Database,
  accountId: string,
  limit: number = 50,
  offset: number = 0
): Promise<unknown[]> {
  const safeLimit = Math.max(1, Math.min(200, limit))
  const safeOffset = Math.max(0, offset)

  const result = await db
    .prepare(
      `
      SELECT je.*, tl.amount, tl.direction, tl.created_at
      FROM transaction_lines tl
      JOIN journal_entries je ON je.id = tl.journal_entry_id
      WHERE tl.account_id = ?
      ORDER BY tl.created_at DESC
      LIMIT ? OFFSET ?
    `
    )
    .bind(accountId, safeLimit, safeOffset)
    .all()

  return (result as { results?: unknown[] }).results ?? []
}

/**
 * Create a simple transfer between two accounts
 * Wrapper around createJournalEntry for common use case
 *
 * @param db - D1 database instance
 * @param tenantId - Tenant identifier
 * @param fromAccountId - Source account ID
 * @param toAccountId - Destination account ID
 * @param amount - Amount to transfer
 * @param description - Transaction description
 * @param idempotencyKey - Optional idempotency key
 * @returns Journal entry ID
 */
export async function transfer(
  db: D1Database,
  tenantId: string,
  fromAccountId: string,
  toAccountId: string,
  amount: number,
  description: string,
  idempotencyKey?: string
): Promise<string> {
  // Validate double-entry
  const lines = [
    { accountId: fromAccountId, amount, direction: -1 },
    { accountId: toAccountId, amount, direction: 1 },
  ]

  if (!validateDoubleEntry(lines)) {
    throw new HttpError('INTERNAL_ERROR', 'Transfer validation failed: unbalanced entry')
  }

  // Check source balance
  await requireBalance(db, fromAccountId, amount, 'Insufficient funds for transfer')

  return createJournalEntry(db, tenantId, description, 'transfer', lines, idempotencyKey)
}
