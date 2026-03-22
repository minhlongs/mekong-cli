/**
 * API Contract Testing Service — CRUD, validation, breaking change detection, compliance
 * Used by api-contract-testing route (X-Admin-Key protected)
 */

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type DB = any;

interface ContractFilters { status?: string; api_path?: string }
interface ContractData {
  name: string; api_path: string; method?: string; version?: string;
  schema_json?: string; request_schema_json?: string; response_schema_json?: string; status?: string;
}

/** List contracts with optional filters */
async function listContracts(db: DB, filters: ContractFilters = {}) {
  const conditions: string[] = [];
  if (filters.status) conditions.push(`status = '${filters.status}'`);
  if (filters.api_path) conditions.push(`api_path = '${filters.api_path}'`);
  const where = conditions.length ? `WHERE ${conditions.join(' AND ')}` : '';
  const { results } = await db
    .prepare(`SELECT * FROM api_contracts ${where} ORDER BY created_at DESC`)
    .all();
  return { contracts: results, total: results.length };
}

/** Get single contract by id */
async function getContract(db: DB, id: string) {
  return db.prepare('SELECT * FROM api_contracts WHERE id = ?').bind(id).first();
}

/** Create new contract */
async function createContract(db: DB, data: ContractData) {
  const id = crypto.randomUUID();
  const now = new Date().toISOString();
  await db.prepare(
    `INSERT INTO api_contracts (id, name, api_path, method, version, schema_json, request_schema_json, response_schema_json, status, created_at, updated_at)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`
  ).bind(
    id, data.name, data.api_path, data.method ?? 'GET', data.version ?? '1.0.0',
    data.schema_json ?? '{}', data.request_schema_json ?? '{}',
    data.response_schema_json ?? '{}', data.status ?? 'active', now, now
  ).run();
  return getContract(db, id);
}

/** Detect schema breaking changes between old and new contract data */
async function detectBreakingChanges(db: DB, contractId: string, oldContract: any, newData: Partial<ContractData>) {
  const schemaFields = ['schema_json', 'request_schema_json', 'response_schema_json'];
  for (const field of schemaFields) {
    const oldVal = oldContract[field] ?? '{}';
    const newVal = (newData as any)[field];
    if (newVal && newVal !== oldVal) {
      await db.prepare(
        `INSERT INTO breaking_changes (id, contract_id, change_type, description, old_schema, new_schema, severity, detected_at)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?)`
      ).bind(
        crypto.randomUUID(), contractId, 'schema_change',
        `Schema field '${field}' modified in contract`, oldVal, newVal,
        'major', new Date().toISOString()
      ).run();
    }
  }
}

/** Update contract fields and detect breaking changes */
async function updateContract(db: DB, id: string, data: Partial<ContractData>) {
  const old = await getContract(db, id);
  if (!old) return null;
  const now = new Date().toISOString();
  const keys = Object.keys(data).filter((k) => k in old);
  if (keys.length) {
    const fields = keys.map((k) => `${k} = ?`).join(', ');
    const values = keys.map((k) => (data as Record<string, unknown>)[k]);
    await db.prepare(`UPDATE api_contracts SET ${fields}, updated_at = ? WHERE id = ?`).bind(...values, now, id).run();
    await detectBreakingChanges(db, id, old, data);
  }
  return getContract(db, id);
}

/** Delete contract by id */
async function deleteContract(db: DB, id: string) {
  await db.prepare('DELETE FROM api_contracts WHERE id = ?').bind(id).run();
  return { deleted: true };
}

/** Validate contract schema — checks for required fields and valid JSON */
async function validateContract(db: DB, id: string) {
  const contract = await getContract(db, id);
  if (!contract) return null;
  const errors: string[] = [];
  const warnings: string[] = [];
  const schemaFields = ['schema_json', 'request_schema_json', 'response_schema_json'];
  for (const field of schemaFields) {
    const raw = contract[field] ?? '{}';
    try { JSON.parse(raw); } catch { errors.push(`Invalid JSON in ${field}`); }
    if (raw === '{}') warnings.push(`${field} is empty`);
  }
  if (!contract.api_path?.startsWith('/')) errors.push('api_path must start with /');
  const validMethods = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE'];
  if (!validMethods.includes(contract.method)) warnings.push(`Unusual HTTP method: ${contract.method}`);
  const validationId = crypto.randomUUID();
  const status = errors.length ? 'failed' : 'passed';
  await db.prepare(
    `INSERT INTO contract_validations (id, contract_id, validation_status, errors_json, warnings_json, validated_at)
     VALUES (?, ?, ?, ?, ?, ?)`
  ).bind(validationId, id, status, JSON.stringify(errors), JSON.stringify(warnings), new Date().toISOString()).run();
  return { id: validationId, contract_id: id, validation_status: status, errors, warnings };
}

/** List validations for a contract */
async function listValidations(db: DB, contractId: string) {
  const { results } = await db
    .prepare('SELECT * FROM contract_validations WHERE contract_id = ? ORDER BY validated_at DESC')
    .bind(contractId).all();
  return { validations: results };
}

/** List breaking changes with optional filters */
async function listBreakingChanges(db: DB, filters: { severity?: string; acknowledged?: string } = {}) {
  const conditions: string[] = [];
  if (filters.severity) conditions.push(`severity = '${filters.severity}'`);
  if (filters.acknowledged !== undefined) conditions.push(`acknowledged = ${filters.acknowledged === 'true' ? 1 : 0}`);
  const where = conditions.length ? `WHERE ${conditions.join(' AND ')}` : '';
  const { results } = await db
    .prepare(`SELECT * FROM breaking_changes ${where} ORDER BY detected_at DESC`)
    .all();
  return { breaking_changes: results, total: results.length };
}

/** Acknowledge a breaking change */
async function acknowledgeBreakingChange(db: DB, id: string) {
  const change = await db.prepare('SELECT * FROM breaking_changes WHERE id = ?').bind(id).first();
  if (!change) return null;
  await db.prepare('UPDATE breaking_changes SET acknowledged = 1 WHERE id = ?').bind(id).run();
  return { ...change, acknowledged: 1 };
}

/** Overall contract compliance report */
async function getComplianceReport(db: DB) {
  const [contractStats, validationStats, changeStats] = await Promise.all([
    db.prepare('SELECT status, COUNT(*) as count FROM api_contracts GROUP BY status').all(),
    db.prepare('SELECT validation_status, COUNT(*) as count FROM contract_validations GROUP BY validation_status').all(),
    db.prepare('SELECT severity, COUNT(*) as count FROM breaking_changes WHERE acknowledged = 0 GROUP BY severity').all(),
  ]);
  const totalContracts = contractStats.results.reduce((sum: number, r: any) => sum + r.count, 0);
  const passedValidations = validationStats.results.find((r: any) => r.validation_status === 'passed')?.count ?? 0;
  const totalValidations = validationStats.results.reduce((sum: number, r: any) => sum + r.count, 0);
  const complianceRate = totalValidations > 0 ? Math.round((passedValidations / totalValidations) * 100) : 0;
  return {
    total_contracts: totalContracts,
    contract_by_status: contractStats.results,
    validation_by_status: validationStats.results,
    unacknowledged_breaking_changes: changeStats.results,
    compliance_rate_pct: complianceRate,
  };
}

/** Admin dashboard overview */
async function getAdminOverview(db: DB) {
  const [contracts, validations, changes] = await Promise.all([
    db.prepare('SELECT COUNT(*) as count FROM api_contracts').first(),
    db.prepare('SELECT COUNT(*) as count FROM contract_validations WHERE validation_status = ?').bind('failed').first(),
    db.prepare('SELECT COUNT(*) as count FROM breaking_changes WHERE acknowledged = 0').first(),
  ]);
  const passedRow = await db.prepare('SELECT COUNT(*) as count FROM contract_validations WHERE validation_status = ?').bind('passed').first();
  const totalVal = (validations?.count ?? 0) + (passedRow?.count ?? 0);
  const complianceRate = totalVal > 0 ? Math.round(((passedRow?.count ?? 0) / totalVal) * 100) : 100;
  return {
    total_contracts: contracts?.count ?? 0,
    failed_validations: validations?.count ?? 0,
    unacknowledged_breaking_changes: changes?.count ?? 0,
    compliance_rate_pct: complianceRate,
  };
}

export const apiContractTestingService = {
  listContracts, createContract, getContract, updateContract, deleteContract,
  validateContract, listValidations, listBreakingChanges, acknowledgeBreakingChange,
  getComplianceReport, getAdminOverview,
};
