#!/usr/bin/env node
/**
 * trace-agent.js
 * Appends an agent trace entry to ~/.system/trace.log.
 *
 * Usage:
 *   node trace-agent.js <agent_id> <task_id> <model> <input_tok> <output_tok> <duration_ms> <status>
 *
 * Example:
 *   node trace-agent.js coder_1 task_123 qwen3.6:35b 1500 500 12450 success
 *
 * Output:
 *   Prints the appended trace line to stdout.
 */

const fs = require('fs');
const path = require('path');

const SYSTEM_DIR = path.resolve(process.env.HOME || '~', '.system');
const TRACE_LOG = path.join(SYSTEM_DIR, 'trace.log');

// -------------------------------------------------------
// Helpers
// -------------------------------------------------------

function die(msg, code = 1) {
  console.error(`[ERROR] ${msg}`);
  process.exit(code);
}

function iso8601() {
  return new Date().toISOString().replace('T', ' ').replace(/\.\d+Z/, '');
}

// -------------------------------------------------------
// Arg Validation
// -------------------------------------------------------

const args = process.argv.slice(2);

if (args.length < 7) {
  console.error(`
Usage: node trace-agent.js <agent_id> <task_id> <model> <input_tok> <output_tok> <duration_ms> <status>

Arguments:
  agent_id     Agent identifier (e.g., coder_1)
  task_id      Task identifier (e.g., task_123)
  model        Model name (e.g., qwen3.6:35b)
  input_tok    Input token count (integer >= 0)
  output_tok   Output token count (integer >= 0)
  duration_ms  Duration in milliseconds (integer >= 0)
  status       Status string (e.g., success, error, timeout)

Example:
  node trace-agent.js coder_1 task_123 qwen3.6:35b 1500 500 12450 success
`);
  process.exit(1);
}

const [agent_id, task_id, model, input_tok, output_tok, duration_ms, status] = args;

// Validate numeric fields
const inputVal = parseInt(input_tok, 10);
if (isNaN(inputVal) || inputVal < 0) die(`Invalid input_tok: "${input_tok}" — must be non-negative integer`);

const outputVal = parseInt(output_tok, 10);
if (isNaN(outputVal) || outputVal < 0) die(`Invalid output_tok: "${output_tok}" — must be non-negative integer`);

const durationVal = parseInt(duration_ms, 10);
if (isNaN(durationVal) || durationVal < 0) die(`Invalid duration_ms: "${duration_ms}" — must be non-negative integer`);

if (!agent_id) die('agent_id is required');
if (!task_id) die('task_id is required');
if (!model) die('model is required');
if (!status) die('status is required');

// -------------------------------------------------------
// Append to trace.log
// -------------------------------------------------------

const timestamp = iso8601();
const line = `${timestamp} | ${agent_id} | ${task_id} | ${model} | ${inputVal} | ${outputVal} | ${durationVal} | ${status}`;

// Ensure directory exists
if (!fs.existsSync(SYSTEM_DIR)) {
  fs.mkdirSync(SYSTEM_DIR, { recursive: true });
}

// Ensure trace.log exists with header
if (!fs.existsSync(TRACE_LOG)) {
  const header = [
    '# Mekong AI OS Trace Log',
    '# Format: ISO_TIMESTAMP | AGENT_ID | TASK_ID | MODEL | INPUT_TOKENS | OUTPUT_TOKENS | DURATION_MS | STATUS',
    `# Initialized: ${new Date().toISOString().slice(0, 10)}`,
    ''
  ].join('\n');
  fs.writeFileSync(TRACE_LOG, header, 'utf-8');
}

fs.appendFileSync(TRACE_LOG, line + '\n', 'utf-8');

console.log(line);
