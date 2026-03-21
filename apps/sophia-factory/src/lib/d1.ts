/**
 * Cloudflare D1 Database Client
 * Used for all data operations (organizations, proposals, brand voices, etc.)
 * 
 * Supabase is used for Auth ONLY (via supabase.ts)
 */

import type { HonoContext } from '../types/error'

export type Organization = {
  id: string
  name: string
  slug: string
  plan: string
  proposals_remaining: number
  created_at: string
}

export type User = {
  id: string
  email: string
  org_id: string | null
  role: string
  created_at: string
}

export type BrandVoice = {
  id: string
  org_id: string
  training_docs_count: number
  model_status: string
  voice_characteristics: string | null  // JSON string
  created_at: string
}

export type Proposal = {
  id: string
  org_id: string
  title: string
  client_name: string | null
  status: string
  content: string | null  // JSON string
  created_at: string
}

export type TrainingDocument = {
  id: string
  org_id: string
  file_url: string
  file_name: string | null
  file_type: string | null
  processed: number
  content_text: string | null
  embedding: string | null  // JSON array string
  created_at: string
}

/**
 * Get D1 database from context
 */
export function getDB(c: HonoContext) {
  return c.env.DB
}

/**
 * Create organization
 */
export async function createOrganization(
  db: D1Database,
  name: string,
  slug: string
): Promise<Organization> {
  const id = crypto.randomUUID()
  await db
    .prepare('INSERT INTO organizations (id, name, slug) VALUES (?, ?, ?)')
    .bind(id, name, slug)
    .run()
  
  return {
    id,
    name,
    slug,
    plan: 'starter',
    proposals_remaining: 10,
    created_at: new Date().toISOString()
  }
}

/**
 * Get organization by slug
 */
export async function getOrganizationBySlug(
  db: D1Database,
  slug: string
): Promise<Organization | null> {
  return await db
    .prepare('SELECT * FROM organizations WHERE slug = ?')
    .bind(slug)
    .first()
}

/**
 * Get organization by ID
 */
export async function getOrganizationById(
  db: D1Database,
  id: string
): Promise<Organization | null> {
  return await db
    .prepare('SELECT * FROM organizations WHERE id = ?')
    .bind(id)
    .first()
}

/**
 * Link user to Supabase Auth
 */
export async function linkUser(
  db: D1Database,
  supabaseUserId: string,
  email: string,
  orgId: string,
  role: string = 'member'
): Promise<void> {
  await db
    .prepare('INSERT INTO users (id, email, org_id, role) VALUES (?, ?, ?, ?)')
    .bind(supabaseUserId, email, orgId, role)
    .run()
}

/**
 * Get user by Supabase Auth ID
 */
export async function getUserById(
  db: D1Database,
  id: string
): Promise<User | null> {
  return await db
    .prepare('SELECT * FROM users WHERE id = ?')
    .bind(id)
    .first()
}

/**
 * Create proposal
 */
export async function createProposal(
  db: D1Database,
  orgId: string,
  title: string,
  clientName?: string
): Promise<Proposal> {
  const id = crypto.randomUUID()
  await db
    .prepare('INSERT INTO proposals (id, org_id, title, client_name) VALUES (?, ?, ?, ?)')
    .bind(id, orgId, title, clientName)
    .run()
  
  return {
    id,
    org_id: orgId,
    title,
    client_name: clientName || null,
    status: 'draft',
    content: null,
    created_at: new Date().toISOString()
  }
}

/**
 * Get proposals by org
 */
export async function getProposalsByOrg(
  db: D1Database,
  orgId: string
): Promise<Proposal[]> {
  const { results } = await db
    .prepare('SELECT * FROM proposals WHERE org_id = ? ORDER BY created_at DESC')
    .bind(orgId)
    .all()
  return results as Proposal[]
}

/**
 * Store brand voice
 */
export async function storeBrandVoice(
  db: D1Database,
  orgId: string,
  voiceCharacteristics: Record<string, unknown>
): Promise<void> {
  const id = crypto.randomUUID()
  await db
    .prepare('INSERT INTO brand_voices (id, org_id, voice_characteristics) VALUES (?, ?, ?)')
    .bind(id, orgId, JSON.stringify(voiceCharacteristics))
    .run()
}

/**
 * Get brand voice by org
 */
export async function getBrandVoiceByOrg(
  db: D1Database,
  orgId: string
): Promise<BrandVoice | null> {
  return await db
    .prepare('SELECT * FROM brand_voices WHERE org_id = ?')
    .bind(orgId)
    .first()
}

/**
 * Store training document with embedding
 */
export async function storeTrainingDocument(
  db: D1Database,
  orgId: string,
  fileUrl: string,
  fileName: string,
  fileType: string,
  contentText: string,
  embedding: number[]
): Promise<void> {
  const id = crypto.randomUUID()
  await db
    .prepare(`INSERT INTO training_documents 
      (id, org_id, file_url, file_name, file_type, content_text, embedding) 
      VALUES (?, ?, ?, ?, ?, ?, ?)`)
    .bind(id, orgId, fileUrl, fileName, fileType, contentText, JSON.stringify(embedding))
    .run()
}

/**
 * Similarity search for training documents (SQLite cosine similarity)
 */
export async function searchSimilarDocuments(
  db: D1Database,
  orgId: string,
  queryEmbedding: number[],
  limit: number = 5
): Promise<TrainingDocument[]> {
  const { results } = await db
    .prepare(`
      SELECT *, 
        (1 - (
          SELECT SUM(
            CAST(json_each.value AS REAL) * CAST(
              (SELECT json_each.value FROM json_each(training_documents.embedding) LIMIT 1 OFFSET 0)
            AS REAL)
          ) / (
            sqrt(SUM(CAST(json_each.value AS REAL) * CAST(json_each.value AS REAL))) *
            sqrt(SUM(CAST(
              (SELECT json_each.value FROM json_each(?) LIMIT 1)
            AS REAL) * CAST(
              (SELECT json_each.value FROM json_each(?) LIMIT 1)
            AS REAL)))
          )
        )) as similarity
      FROM training_documents, json_each(training_documents.embedding)
      WHERE org_id = ?
      ORDER BY similarity DESC
      LIMIT ?
    `)
    .bind(JSON.stringify(queryEmbedding), JSON.stringify(queryEmbedding), orgId, limit)
    .all()
  
  return results as TrainingDocument[]
}
