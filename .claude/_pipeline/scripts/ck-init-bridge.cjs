#!/usr/bin/env node
/**
 * CK-Init Bridge — Mekong Session Bootstrap
 *
 * Runs `mekong init` (wizard) to bootstrap .mekong/company.json,
 * then reads and validates the structured output.
 *
 * Graceful fallback: if the `mekong` binary is not found, prints guidance
 * and exits 0 (soft failure) rather than crashing the parent agent.
 *
 * Usage: node ck-init-bridge.cjs [--force]
 *
 * --force    Re-run init even if .mekong/company.json already exists
 *
 * 🏯 Binh Pháp — "Duệ nhận biết" — Discern before acting
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

// =====================================================
// CONFIGURATION
// =====================================================

const CONFIG = {
  /** Mekong CLI binary name (prefer absolute if MEKONG_BIN env var is set) */
  MEKONG_BIN: process.env.MEKONG_BIN || 'mekong',
  /** Working directory for the mekong command */
  CWD: process.cwd(),
  /** Path to the company JSON produced by `mekong init` */
  COMPANY_JSON: path.join(process.cwd(), '.mekong', 'company.json'),
  /** Fields used for validation (name from company.json) */
  REQUIRED_FIELDS: ['name'],
  /** Init timeout (ms) — wizard should complete quickly */
  INIT_TIMEOUT_MS: 30_000,
};

// =====================================================
// HELPERS
// =====================================================

/**
 * Detect whether the mekong binary is available.
 */
function isMekongAvailable() {
  try {
    execSync(`which ${CONFIG.MEKONG_BIN}`, {
      encoding: 'utf-8',
      stdio: ['pipe', 'pipe', 'pipe'],
    });
    return true;
  } catch {
    return false;
  }
}

/**
 * Print guidance for a missing mekong binary and exit 0 (soft fail).
 */
function printMissingMekongGuidance() {
  console.log(JSON.stringify({
    ok: false,
    soft_fail: true,
    reason: 'mekong_binary_not_found',
    guidance: [
      'Mekong CLI is not installed or not in PATH.',
      'Install: git clone https://github.com/OpenClaw/mekong-cli.git && cd mekong-cli && ./scripts/install.sh',
      'Or set MEKONG_BIN env var to the absolute path of the mekong binary.',
      'See: https://github.com/OpenClaw/mekong-cli#installation',
    ],
  }, null, 2));
}

/**
 * Validate required fields exist in the company JSON.
 * @param {object} data
 * @returns {{valid: boolean, missing: string[]}}
 */
function validateOutput(data) {
  if (typeof data !== 'object' || data === null || Array.isArray(data)) {
    return { valid: false, missing: ['root must be an object'] };
  }
  const missing = CONFIG.REQUIRED_FIELDS.filter(f => !(f in data) || !data[f]);
  return { valid: missing.length === 0, missing };
}

/**
 * Read .mekong/company.json if it exists.
 * @returns {{data: object | null, error: string | null}}
 */
function readCompanyJson() {
  try {
    if (!fs.existsSync(CONFIG.COMPANY_JSON)) {
      return { data: null, error: 'company_json_not_found' };
    }
    const raw = fs.readFileSync(CONFIG.COMPANY_JSON, 'utf-8');
    const data = JSON.parse(raw);
    return { data, error: null };
  } catch (err) {
    return { data: null, error: err.message };
  }
}

// =====================================================
// MAIN EXECUTION
// =====================================================

function main() {
  const args = process.argv.slice(2);
  const force = args.includes('--force');

  // Check if company.json already exists
  const existing = readCompanyJson();

  if (existing.data && !force) {
    // Already initialized — return current state
    const validation = validateOutput(existing.data);
    console.log(JSON.stringify({
      ok: true,
      initialized: true,
      already_initialized: true,
      company_name: existing.data.name,
      product_type: existing.data.model || null,
      stage: existing.data.stage || null,
      valid: validation.valid,
    }, null, 2));
    return;
  }

  // Gateway check: is mekong available?
  if (!isMekongAvailable()) {
    printMissingMekongGuidance();
    process.exit(0);
  }

  // Run `mekong init` (interactive wizard)
  // Note: This creates .mekong/company.json in the CWD
  let stdout;
  try {
    stdout = execSync(`${CONFIG.MEKONG_BIN} init`, {
      encoding: 'utf-8',
      cwd: CONFIG.CWD,
      timeout: CONFIG.INIT_TIMEOUT_MS,
      stdio: ['pipe', 'pipe', 'pipe'],
    });
  } catch (error) {
    const stderr = error.stderr?.toString() || error.message || 'Unknown error';
    console.log(JSON.stringify({
      ok: false,
      soft_fail: false,
      reason: 'mekong_init_failed',
      error: stderr,
      command: `${CONFIG.MEKONG_BIN} init`,
    }, null, 2));
    process.exit(1);
  }

  // Read the generated company.json
  const { data, error } = readCompanyJson();

  if (!data || error) {
    console.log(JSON.stringify({
      ok: false,
      soft_fail: false,
      reason: 'company_json_read_failed',
      error,
      path: CONFIG.COMPANY_JSON,
      raw_output: (stdout || '').substring(0, 300),
    }, null, 2));
    process.exit(1);
  }

  // Validate required fields
  const validation = validateOutput(data);
  if (!validation.valid) {
    console.log(JSON.stringify({
      ok: false,
      soft_fail: false,
      reason: 'validation_failed',
      missing_fields: validation.missing,
      received_keys: Object.keys(data),
      raw: data,
    }, null, 2));
    process.exit(1);
  }

  // Success
  console.log(JSON.stringify({
    ok: true,
    initialized: true,
    already_initialized: false,
    company_name: data.name,
    product_type: data.model || null,
    stage: data.stage || null,
    path: CONFIG.COMPANY_JSON,
  }, null, 2));
}

main();
