/**
 * Environment Service — per-tenant environment management (production/staging/etc.)
 * Supports env CRUD, variable upsert with secret masking, clone, and default seeding
 */

import type { D1Database } from '@cloudflare/workers-types';

export type EnvType = 'production' | 'staging' | 'development' | 'testing';

export interface Environment {
  id: string;
  tenant_id: string;
  name: string;
  env_type: EnvType;
  description?: string;
  config: string; // JSON
  api_base_url?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface EnvVariable {
  id: string;
  environment_id: string;
  tenant_id: string;
  key: string;
  value: string; // masked if secret
  is_secret: boolean;
  created_at: string;
  updated_at: string;
}

export interface CreateEnvInput {
  name: string;
  envType: EnvType;
  description?: string;
  config?: Record<string, unknown>;
  apiBaseUrl?: string;
}

export interface UpdateEnvInput {
  name?: string;
  description?: string;
  config?: Record<string, unknown>;
  apiBaseUrl?: string;
  isActive?: boolean;
}

/** Mask secret values: show only last 4 chars */
function maskSecret(value: string): string {
  if (value.length <= 4) return '****';
  return `****${value.slice(-4)}`;
}

export async function createEnvironment(
  db: D1Database,
  tenantId: string,
  input: CreateEnvInput
): Promise<Environment> {
  const id = crypto.randomUUID();
  const config = JSON.stringify(input.config ?? {});
  await db.prepare(
    `INSERT INTO environments (id, tenant_id, name, env_type, description, config, api_base_url)
     VALUES (?, ?, ?, ?, ?, ?, ?)`
  ).bind(id, tenantId, input.name, input.envType, input.description ?? null, config, input.apiBaseUrl ?? null).run();
  return getEnvironment(db, tenantId, id) as Promise<Environment>;
}

export async function getEnvironments(db: D1Database, tenantId: string): Promise<Environment[]> {
  const { results } = await db.prepare(
    `SELECT * FROM environments WHERE tenant_id = ? ORDER BY created_at ASC`
  ).bind(tenantId).all<Environment>();
  return results;
}

export async function getEnvironment(
  db: D1Database,
  tenantId: string,
  envId: string
): Promise<Environment | null> {
  return db.prepare(
    `SELECT * FROM environments WHERE id = ? AND tenant_id = ?`
  ).bind(envId, tenantId).first<Environment>();
}

export async function updateEnvironment(
  db: D1Database,
  tenantId: string,
  envId: string,
  input: UpdateEnvInput
): Promise<Environment | null> {
  const env = await getEnvironment(db, tenantId, envId);
  if (!env) return null;
  const config = input.config !== undefined ? JSON.stringify(input.config) : env.config;
  const isActive = input.isActive !== undefined ? (input.isActive ? 1 : 0) : (env.is_active ? 1 : 0);
  await db.prepare(
    `UPDATE environments SET name=?, description=?, config=?, api_base_url=?, is_active=?, updated_at=datetime('now') WHERE id=? AND tenant_id=?`
  ).bind(input.name ?? env.name, input.description ?? env.description ?? null, config, input.apiBaseUrl ?? env.api_base_url ?? null, isActive, envId, tenantId).run();
  return getEnvironment(db, tenantId, envId);
}

/** Delete environment — blocks deletion of production type */
export async function deleteEnvironment(
  db: D1Database,
  tenantId: string,
  envId: string
): Promise<{ deleted: boolean; error?: string }> {
  const env = await getEnvironment(db, tenantId, envId);
  if (!env) return { deleted: false, error: 'Not found' };
  if (env.env_type === 'production') return { deleted: false, error: 'Cannot delete production environment' };
  await db.prepare(`DELETE FROM environment_variables WHERE environment_id=? AND tenant_id=?`).bind(envId, tenantId).run();
  await db.prepare(`DELETE FROM environments WHERE id=? AND tenant_id=?`).bind(envId, tenantId).run();
  return { deleted: true };
}

export async function setVariable(
  db: D1Database,
  tenantId: string,
  envId: string,
  key: string,
  value: string,
  isSecret = false
): Promise<EnvVariable> {
  const existing = await db.prepare(
    `SELECT id FROM environment_variables WHERE environment_id=? AND key=? AND tenant_id=?`
  ).bind(envId, key, tenantId).first<{ id: string }>();
  if (existing) {
    await db.prepare(
      `UPDATE environment_variables SET value=?, is_secret=?, updated_at=datetime('now') WHERE id=?`
    ).bind(value, isSecret ? 1 : 0, existing.id).run();
    return getVariableRow(db, existing.id, isSecret, value);
  }
  const id = crypto.randomUUID();
  await db.prepare(
    `INSERT INTO environment_variables (id, environment_id, tenant_id, key, value, is_secret)
     VALUES (?, ?, ?, ?, ?, ?)`
  ).bind(id, envId, tenantId, key, value, isSecret ? 1 : 0).run();
  return getVariableRow(db, id, isSecret, value);
}

async function getVariableRow(db: D1Database, id: string, isSecret: boolean, rawValue: string): Promise<EnvVariable> {
  const row = await db.prepare(`SELECT * FROM environment_variables WHERE id=?`).bind(id).first<EnvVariable>();
  if (!row) throw new Error('Variable not found after write');
  return { ...row, value: isSecret ? maskSecret(rawValue) : rawValue };
}

/** List variables — secrets masked */
export async function getVariables(db: D1Database, tenantId: string, envId: string): Promise<EnvVariable[]> {
  const { results } = await db.prepare(
    `SELECT * FROM environment_variables WHERE environment_id=? AND tenant_id=? ORDER BY key ASC`
  ).bind(envId, tenantId).all<EnvVariable>();
  return results.map((v) => ({ ...v, value: v.is_secret ? maskSecret(v.value) : v.value }));
}

export async function deleteVariable(
  db: D1Database,
  tenantId: string,
  envId: string,
  key: string
): Promise<boolean> {
  const result = await db.prepare(
    `DELETE FROM environment_variables WHERE environment_id=? AND tenant_id=? AND key=?`
  ).bind(envId, tenantId, key).run();
  return (result.meta?.changes ?? 0) > 0;
}

/** Clone environment with all its variables (non-secret values only; secrets reset) */
export async function cloneEnvironment(
  db: D1Database,
  tenantId: string,
  sourceEnvId: string,
  newName: string,
  newType: EnvType
): Promise<Environment> {
  const source = await getEnvironment(db, tenantId, sourceEnvId);
  if (!source) throw new Error('Source environment not found');
  const newEnv = await createEnvironment(db, tenantId, {
    name: newName,
    envType: newType,
    description: source.description ? `Cloned from ${source.name}` : undefined,
    config: JSON.parse(source.config ?? '{}'),
    apiBaseUrl: source.api_base_url ?? undefined,
  });
  // Clone non-secret variables only
  const { results: vars } = await db.prepare(
    `SELECT * FROM environment_variables WHERE environment_id=? AND tenant_id=? AND is_secret=0`
  ).bind(sourceEnvId, tenantId).all<EnvVariable>();
  for (const v of vars) {
    await setVariable(db, tenantId, newEnv.id, v.key, v.value, false);
  }
  return newEnv;
}

/** Seed default production + staging environments for a new tenant */
export async function seedDefaultEnvironments(db: D1Database, tenantId: string): Promise<Environment[]> {
  const existing = await getEnvironments(db, tenantId);
  if (existing.length > 0) return existing;
  const prod = await createEnvironment(db, tenantId, { name: 'production', envType: 'production', description: 'Production environment' });
  const staging = await createEnvironment(db, tenantId, { name: 'staging', envType: 'staging', description: 'Staging environment' });
  return [prod, staging];
}
