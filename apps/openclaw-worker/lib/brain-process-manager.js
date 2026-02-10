/**
 * Brain Process Manager v26.0 — Dual-mode, dual-engine CC CLI brain
 *
 * Engines: 'antigravity' (port 8080, default) or 'qwen' (port 8081, Qwen Bridge)
 *   Set TOM_HUM_ENGINE=qwen to use Qwen models via DashScope.
 *
 * Modes: 'direct' (claude -p, default) or 'tmux' (persistent session, fallback)
 *   Set TOM_HUM_BRAIN_MODE=tmux to activate tmux mode.
 *
 * Exports (unchanged API): spawnBrain, killBrain, isBrainAlive, runMission, log
 */

const { spawn, execSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const config = require('../config');

let missionCount = 0;
let currentProc = null;

// --- Shared helpers ---

function getApiKey() {
  if (process.env.ANTHROPIC_API_KEY) return process.env.ANTHROPIC_API_KEY;
  const keyFile = path.join(process.env.HOME || '', '.mekong', 'api-key');
  try { return fs.readFileSync(keyFile, 'utf-8').trim(); } catch (e) { return ''; }
}

function log(msg) {
  const timestamp = new Date().toISOString().slice(11, 19);
  const formatted = `[${timestamp}] [tom-hum] ${msg}\n`;
  process.stderr.write(formatted);
  try { fs.appendFileSync(config.LOG_FILE, formatted); } catch (e) {}
}

function sleep(ms) { return new Promise((r) => setTimeout(r, ms)); }

function tmux(cmd) {
  return execSync(`tmux ${cmd}`, { encoding: 'utf-8', timeout: 10000 }).trim();
}

// --- Engine helpers ---

const isQwen = config.ENGINE === 'qwen';

function getProxyPort() {
  return isQwen ? config.QWEN_PROXY_PORT : config.PROXY_PORT;
}

function getModelName() {
  return isQwen ? config.QWEN_MODEL_NAME : config.MODEL_NAME;
}

function getEngineLabel() {
  return isQwen ? `qwen (port ${config.QWEN_PROXY_PORT})` : `antigravity (port ${config.PROXY_PORT})`;
}

// =============================================================================
// DIRECT MODE — claude -p per mission (default)
// =============================================================================

function spawnBrainDirect() {
  log(`BRAIN v26.0: Direct mode (claude -p) | Engine: ${getEngineLabel()}`);
  log('All ClaudeKit agents/tools supported. Watch via: node lib/live-mission-viewer.js');
}

function killBrainDirect() {
  if (currentProc) {
    try { currentProc.kill('SIGTERM'); } catch (e) {}
    currentProc = null;
  }
}

function isBrainAliveDirect() { return true; }

function runMissionDirect(prompt, projectDir, timeoutMs) {
  return new Promise((resolve) => {
    missionCount++;
    const num = missionCount;
    const startTime = Date.now();
    log(`MISSION #${num}: ${prompt.slice(0, 150)}...`);
    log(`PROJECT: ${projectDir} | MODE: direct | ENGINE: ${getEngineLabel()}`);

    const apiKey = getApiKey();
    const proxyPort = getProxyPort();
    const modelName = getModelName();
    const proc = spawn('claude', [
      '-p', prompt,
      '--model', modelName,
      '--dangerously-skip-permissions',
    ], {
      cwd: projectDir,
      env: {
        ...process.env,
        ANTHROPIC_BASE_URL: `http://127.0.0.1:${proxyPort}`,
        ANTHROPIC_API_KEY: apiKey,
      },
      stdio: ['ignore', 'pipe', 'pipe'],
    });

    currentProc = proc;
    let output = '';

    proc.stdout.on('data', (chunk) => {
      const text = chunk.toString();
      output += text;
      try { fs.appendFileSync(config.LOG_FILE, text); } catch (e) {}
    });

    proc.stderr.on('data', (chunk) => {
      const text = chunk.toString();
      try { fs.appendFileSync(config.LOG_FILE, `[stderr] ${text}`); } catch (e) {}
    });

    const timer = setTimeout(() => {
      log(`TIMEOUT: Mission #${num} exceeded ${Math.round(timeoutMs / 1000)}s`);
      try { proc.kill('SIGTERM'); } catch (e) {}
    }, timeoutMs);

    // Status heartbeat every 60s
    const heartbeat = setInterval(() => {
      const elapsed = Math.round((Date.now() - startTime) / 1000);
      log(`Mission #${num} working -- ${elapsed}s`);
    }, 60000);

    proc.on('close', (code) => {
      clearTimeout(timer);
      clearInterval(heartbeat);
      currentProc = null;
      const elapsed = Math.round((Date.now() - startTime) / 1000);
      const success = code === 0;
      log(`${success ? 'COMPLETE' : 'FAILED'}: Mission #${num} (${elapsed}s, exit=${code})`);
      resolve({ success, result: success ? 'done' : `exit_${code}`, elapsed });
    });

    proc.on('error', (err) => {
      clearTimeout(timer);
      clearInterval(heartbeat);
      currentProc = null;
      const elapsed = Math.round((Date.now() - startTime) / 1000);
      log(`ERROR: Mission #${num} spawn failed: ${err.message}`);
      resolve({ success: false, result: `spawn_error: ${err.message}`, elapsed });
    });
  });
}

// =============================================================================
// TMUX MODE — persistent visible session (fallback)
// =============================================================================

function capturePane() {
  try { return tmux(`capture-pane -t ${config.TMUX_SESSION} -p`); } catch (e) { return ''; }
}

function isPromptVisible(paneText) {
  const lines = paneText.split('\n').filter((l) => l.trim());
  if (!lines.length) return false;
  const last = lines[lines.length - 1];
  return last.includes('\u276f') || />\s*$/.test(last);
}

function spawnBrainTmux() {
  log(`BRAIN v26.0: Tmux mode (persistent visible session) | Engine: ${getEngineLabel()}`);
  try { tmux(`kill-session -t ${config.TMUX_SESSION}`); } catch (e) {}
  try { fs.unlinkSync(config.MISSION_FILE); } catch (e) {}
  try { fs.unlinkSync(config.DONE_FILE); } catch (e) {}
  tmux(`new-session -d -s ${config.TMUX_SESSION} -x ${config.TMUX_WIDTH} -y ${config.TMUX_HEIGHT}`);
  const apiKey = getApiKey();
  const proxyPort = getProxyPort();
  const modelName = getModelName();
  const cliCmd = [
    `cd ${config.MEKONG_DIR}`, '&&',
    `ANTHROPIC_BASE_URL=http://127.0.0.1:${proxyPort}`,
    `ANTHROPIC_API_KEY=${apiKey}`,
    'claude', `--model ${modelName}`, '--dangerously-skip-permissions',
  ].join(' ');
  tmux(`send-keys -t ${config.TMUX_SESSION} -l ${JSON.stringify(cliCmd)}`);
  tmux(`send-keys -t ${config.TMUX_SESSION} Enter`);
  log(`Tmux session "${config.TMUX_SESSION}" created — tmux attach to watch`);
}

function killBrainTmux() {
  try { tmux(`kill-session -t ${config.TMUX_SESSION}`); } catch (e) {}
}

function isBrainAliveTmux() {
  try { execSync(`tmux has-session -t ${config.TMUX_SESSION}`, { timeout: 5000 }); return true; }
  catch (e) { return false; }
}

async function waitForPrompt(timeoutMs = 120000) {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    if (isPromptVisible(capturePane())) {
      await sleep(config.PROMPT_DEBOUNCE_MS);
      if (isPromptVisible(capturePane())) return true;
    }
    await sleep(config.POLL_INTERVAL_MS);
  }
  return false;
}

async function runMissionTmux(prompt, projectDir, timeoutMs) {
  missionCount++;
  const num = missionCount;
  const startTime = Date.now();

  if (!isBrainAliveTmux()) {
    log(`Brain dead before mission #${num} — respawning`);
    spawnBrainTmux();
    if (!(await waitForPrompt())) {
      return { success: false, result: 'brain_spawn_timeout', elapsed: 0 };
    }
  }

  log(`MISSION #${num}: ${prompt.slice(0, 150)}...`);
  log(`PROJECT: ${projectDir} | MODE: tmux | ENGINE: ${getEngineLabel()}`);
  tmux(`send-keys -t ${config.TMUX_SESSION} -l ${JSON.stringify(`cd ${projectDir}`)}`);
  tmux(`send-keys -t ${config.TMUX_SESSION} Enter`);
  await sleep(1000);
  tmux(`send-keys -t ${config.TMUX_SESSION} -l ${JSON.stringify(prompt)}`);
  tmux(`send-keys -t ${config.TMUX_SESSION} Enter`);
  await sleep(5000);

  const heartbeat = setInterval(() => {
    log(`Mission #${num} working -- ${Math.round((Date.now() - startTime) / 1000)}s`);
  }, 60000);

  const completed = await waitForPrompt(timeoutMs);
  clearInterval(heartbeat);
  const elapsed = Math.round((Date.now() - startTime) / 1000);

  if (completed) {
    log(`COMPLETE: Mission #${num} (${elapsed}s)`);
    return { success: true, result: 'done', elapsed };
  }
  log(`TIMEOUT: Mission #${num} exceeded ${Math.round(timeoutMs / 1000)}s`);
  return { success: false, result: 'timeout', elapsed };
}

// =============================================================================
// Mode dispatch — export unified API
// =============================================================================

const isDirect = config.BRAIN_MODE === 'direct';

module.exports = {
  spawnBrain:    isDirect ? spawnBrainDirect   : spawnBrainTmux,
  killBrain:     isDirect ? killBrainDirect    : killBrainTmux,
  isBrainAlive:  isDirect ? isBrainAliveDirect : isBrainAliveTmux,
  runMission:    isDirect ? runMissionDirect    : runMissionTmux,
  log,
};
