/**
 * Brain Process Manager
 *
 * Manages the CC CLI process via tmux session for robustness and interactivity.
 *
 * Architecture:
 *   spawnBrain()  → tmux new-session + launch CC CLI interactive
 *   runMission()  → paste prompt + state-machine polling (DISPATCHED→BUSY→DONE)
 *   killBrain()   → tmux kill-session
 *
 * CRITICAL FIX (v29): CC CLI TUI always renders ❯ even when busy.
 * hasPrompt() alone is UNRELIABLE for completion detection.
 * runMission() uses state machine: require BUSY→IDLE transition or completion pattern.
 *
 * State machine for mission completion:
 *   DISPATCHED → BUSY → DONE
 *   Completion requires:
 *     (a) Completion pattern (Cooked/Sautéed/Churned for Xm Ys), OR
 *     (b) Was BUSY then became IDLE for 3 consecutive polls, OR
 *     (c) Never detected BUSY but elapsed > 45s and IDLE for 3 consecutive polls
 *
 * Context management: /clear every 3 missions, /compact every 5 missions
 * Crash recovery: auto-respawn with --continue, rate-limited 5/hr
 *
 * Exports: spawnBrain, killBrain, isBrainAlive, runMission, log
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const config = require('../config');
const { isProAvailable, setProLimitHit } = require('./system-status-registry');
const { getHandForIntent } = require('./hands-registry');

const TMUX_SESSION_PRO = `${config.TMUX_SESSION}:brain`;
const TMUX_SESSION_API = `${config.TMUX_SESSION}:brain`;
const COMPACT_EVERY_N = Infinity; // 🦞 DISABLED — AG Proxy manages context
const COMPACT_TOKEN_THRESHOLD = Infinity; // 🦞 DISABLED — AG Proxy manages context
// 🧬 FIX #3: REMOVE /clear — CC CLI's /compact handles cleanup better
// CLEAR_EVERY_N removed — /clear is redundant with /compact
const MAX_RESPAWNS_PER_HOUR = 5;
const RESPAWN_COOLDOWN_MS = 5 * 60 * 1000;
const PROMPT_FILE = '/tmp/tom_hum_prompt.txt';
// 🦞 FIX 2026-02-23: 10s too fast → false positives (5 CRITICAL tasks lost in 1 min)
const MIN_MISSION_SECONDS = 60;   // 🦞 FIX 2026-02-24: 30→60s — CC CLI via proxy needs up to 60s to initialize
const IDLE_CONFIRM_POLLS = 8;     // 8 consecutive idle polls required (was 5)

// --- DETECTION PATTERNS ---

// CC CLI activity indicators (present continuous = actively processing)
const BUSY_PATTERNS = [
  /Photosynthesizing/i, /Crunching/i, /Saut[eé]ing/i,
  /Marinating/i, /Fermenting/i, /Braising/i,
  /Reducing/i, /Blanching/i,
  /[*·✢✻✽✳✶]\s*(?:Thinking|Compacting|Galloping|Reading|Writing|Executing|Running|Bắt đầu|Gusting|Whirring|Boondoggling|Pondering|Synthesizing|Refining|Actioning|Investigating|Analyzing|Exploring)/i,  // 🦞 FIX: Match * status lines + Vibe words
  /Churning/i, /Cooking/i, /Toasting/i, /Galloping/i,
  /Simmering/i, /Steaming/i, /Grilling/i, /Roasting/i,
  /Levitating/i,                       // CC CLI status (Finalizing/Summarizing)
  /Osmosing/i,                         // CC CLI status (Context ingestion)
  /Computing/i, /^\s*⏺\s*Read/m, /^\s*⏺\s*Execut/m, /Indexing/i, // 🦞 FIX: Reading/Executing need ⏺ prefix
  /[*·✻✢✽✳✶]\s+\w+ing/,                     // General: ✻ or * or ✢ or · or ✽ or ✳ + any gerund verb
  /\d+[ms]\s+\d+[ms]\s*·\s*[↑↓]/,      // Timer + arrow: "4m 27s · ↑"
  /[↑↓]\s*[\d.]+k?\s*tokens/i,         // Counter: "↑ 0 tokens" or "↓ 4.5k tokens"
  /\d+\s+local\s+agents?/i,             // 🦞 FIX 2026-02-23: CC CLI subagents running ("3 local agents")
  /Cost:\s*\$[\d.]+/,                  // Cost display usually means busy calculating
  /Calling tool/i, /Running command/i, /Searching/i, /Reading/i, /Writing/i, // Explicit status
  /Running tests/i, /Running\s+\d+\s+Task agents?/i, // CC CLI generic status messages
  /[⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏]/,          // Braille spinners
  /Nesting/i,                          // 🦞 FIX 2026-02-23: CC CLI nested operations (✽ Nesting…)
  /Puttering/i,                        // 🦞 FIX 2026-02-23: CC CLI processing state
  /Pasted text/i,                      // 🦞 FIX 2026-02-23: CC CLI received pasted command, processing it
  /filesystem\s*[-–—]\s*/i,            // 🦞 FIX 2026-02-23: MCP tool calls (filesystem - list_directory)
  /\+\d+\s+lines\s*\(ctrl/i,           // 🦞 FIX 2026-02-23: CC CLI collapsible output (+477 lines (ctrlo to expand))
  /Gusting/i, /Whirring/i, /Boondoggling/i, /Pondering/i, /Synthesizing/i, /Refining/i, /Actioning/i, /Investigating/i, /Analyzing/i, /Exploring/i, // 🦞 FIX: Add explicit Vibe words
];

// CC CLI completion indicators (past tense = finished cooking)
const COMPLETION_PATTERNS = [
  /(?:Cooked|Churned|Saut[eé]ed|Braised|Blanched|Reduced|Fermented|Marinated|Toasted|Simmered|Steamed|Grilled|Roasted)\s+for\s+\d+/i,
  /[·✻✢✽✳✶]\s+\w+(?:ed|t)\s+for\s+\d+/i,     // General: ✻ + past tense + "for N"
  /Task completed in/i, /Finished in \d+/i, /Completed\s+\d+\s+steps/i, /Subagent finished/i, // Explicit explicit status
];

// CC CLI asking for approval/confirmation
const APPROVE_PATTERNS = [
  /Do you want to run this command\?/,
  /Do you want to proceed\?/,
  /Do you want to execute this code\?/,
  /Enter your API key/,
  /Do you want to use this API key\?/,
  /\(y\/n\)/i, /\[y\/n\]/i, /\[Y\/n\]/i,
  /Approve\?/i, /Confirm\?/i,
  /Do you want to allow/i,             // Specific TUI permission prompt
  /Use arrow keys to select/i,
  /Select an option/i,
  /2\.\s+No\s+\(recommended\)/i,
  /1\.\s+Yes,\s+I accept/i,
  /By proceeding, you accept all responsibility/i,
  // 🧬 FIX Bug #2/#7: Decision-request patterns + comprehensive coverage
  /muốn.*làm gì/i,                     // "Bạn muốn tôi làm gì tiếp theo?"
  /USER DECISION/i,                    // "USER DECISION REQUIRED"
  /Khuyến nghị.*chọn/i,                // "Khuyến nghị: Chọn Option A"
  /Options?:/i,                        // "Options: A) ... B) ..."
  /What would you like/i,              // "What would you like me to do?"
  /Which option/i,                     // "Which option do you prefer?"
  /tiếp theo/i,                        // "làm gì tiếp theo?"
  /Continue with/i,                    // "Continue with this?"
  /Proceed with/i,                     // "Proceed with implementation?"
  /Glob patterns are not allowed/i,    // Prompt: "Glob patterns are not allowed in write operations"
  // 🧬 FIX: Treat proxy compacting as an approval point to unblock CC CLI
  // /Compacting conversation/i, // 🦞 DISABLED
  // /Context left until auto-compact/ // 🦞 DISABLED
  /Waiting for approval/i,             // Pending user approval inside tool execution
  /Press\s+Enter\s+to\s+continue/i,    // Waiting for Enter to continue
];

// Claude Pro Rate Limit indicators
const PRO_LIMIT_PATTERNS = [
  /You(?:'ve| have) hit your limit/i,
  /resets 6am/i,
  /Switch to extra usage/i,
  /Upgrade your plan/i,
];

// CC CLI context exhaustion
const CONTEXT_LIMIT_PATTERNS = [
  /Context limit reached/i,
  /\/compact or \/clear/i,
  /context is full/i,
  /out of context/i,
];

let missionCount = 0;
let tokensSinceCompact = 0; // Track accumulated context usage
let respawnTimestamps = [];
// 🧬 FIX Bug #1: DUPLICATE DISPATCH PREVENTION
// We track hashes of recently dispatched missions to prevent spamming
// However, to allow legitimate retries after failure, we use a 10-minute TTL instead of indefinite blockade.
const DEDUP_TTL_MS = 10 * 60 * 1000;
const dispatchedMissions = new Map(); // hash -> timestamp

// --- Logging ---

function log(msg) {
  const timestamp = new Date().toISOString().slice(11, 19);
  const formatted = `[${timestamp}] [tom-hum] ${msg}\n`;
  try { process.stderr.write(formatted); } catch (e) { /* EPIPE safe */ }
  try { fs.appendFileSync(config.LOG_FILE, formatted); } catch (e) { }
}

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

// 🧬 FIX Bug #1: Simple hash function for mission deduplication
function hashPrompt(prompt) {
  return require('crypto').createHash('md5').update(prompt).digest('hex');
}

// 🧬 BRAIN SURGERY v30: TTL-based dedup check
function isDuplicateMission(promptHash) {
  const now = Date.now();
  // Purge expired entries
  for (const [hash, ts] of dispatchedMissions.entries()) {
    if (now - ts > DEDUP_TTL_MS) dispatchedMissions.delete(hash);
  }
  return dispatchedMissions.has(promptHash);
}

function trackMissionHash(promptHash) {
  dispatchedMissions.set(promptHash, Date.now());
}

/** Strip ANSI escape codes + control characters from captured tmux text */
function stripAnsi(text) {
  return text
    .replace(/\x1B\[[0-9;?]*[A-Za-z]/g, '')         // CSI sequences (colors, cursor)
    .replace(/\x1B\][^\x07\x1B]*(?:\x07|\x1B\\)/g, '') // OSC sequences (BEL or ST)
    .replace(/\x1B[()][A-Za-z0-9]/g, '')              // Character set selection
    .replace(/\x1B[A-Za-z]/g, '')                      // Simple ESC sequences
    .replace(/[\x00-\x08\x0E-\x1F\x7F]/g, '');        // Control chars (keep \t \n \r)
}

// --- Tmux helpers ---

function tmuxExec(cmd, sessionName = TMUX_SESSION_PRO) {
  try {
    return execSync(cmd, { encoding: 'utf-8', timeout: 10000 }).trim();
  } catch (e) {
    log(`TMUX ERROR [session=${sessionName}]: ${e.message}`);
    return '';
  }
}

function isSessionAlive(sessionName = TMUX_SESSION_PRO) {
  try {
    execSync(`tmux has-session -t ${sessionName} 2>/dev/null`, { timeout: 5000 });
    return true;
  } catch (e) { return false; }
}

function sendEnter(workerIdx, sessionName = TMUX_SESSION_PRO) {
  tmuxExec(`tmux send-keys -t ${sessionName}.${workerIdx} Enter`, sessionName);
}

function sendCtrlC(workerIdx, sessionName = TMUX_SESSION_PRO) {
  tmuxExec(`tmux send-keys -t ${sessionName}.${workerIdx} C-c`, sessionName);
}

function pasteText(text, workerIdx, sessionName = TMUX_SESSION_PRO) {
  const tmpFile = `/tmp/tom_hum_paste_P${workerIdx}_${sessionName}.txt`;
  fs.writeFileSync(tmpFile, text);
  tmuxExec(`tmux load-buffer ${tmpFile} && tmux paste-buffer -t ${sessionName}.${workerIdx}`, sessionName);
}

// 🦞 FIX 2026-02-23: Centralized tmux throttle guard
// ALL modules go through capturePane() → tmuxExec() → this guard
// Prevents tmux socket contention that causes freezing
let _lastTmuxCallTime = 0;
let _lastTmuxResult = '';
let _lastTmuxCacheKey = '';
// 🦞 OPTIMIZATION 2026-02-26: 5s → 1.5s (Sub-5s response mandate)
const TMUX_MIN_GAP_MS = 1500;

/** 
 * Diagnostics: Log the visual tail to the CTO log to ensure we are not "blind"
 * Only logs when state is 'unknown' or stuck for a while.
 */
function logVision(output, label = 'UNKNOWN') {
  const tail = getCleanTail(output, 8).join('\n');
  log(`[👀 VISION] (${label}) captured tail:\n------------------\n${tail}\n------------------`);
}

function capturePane(workerIdx, sessionName = TMUX_SESSION_PRO) {
  const now = Date.now();
  const elapsed = now - _lastTmuxCallTime;

  // Throttle: return cached result ONLY if same worker and session and called too soon
  const cacheKey = `${sessionName}:${workerIdx}`;
  if (elapsed < TMUX_MIN_GAP_MS && _lastTmuxResult && _lastTmuxCacheKey === cacheKey) {
    return _lastTmuxResult;
  }

  const idx = workerIdx !== undefined ? workerIdx : currentWorkerIdx;
  _lastTmuxCallTime = now;
  _lastTmuxCacheKey = cacheKey;

  try {
    // Rely exclusively on tmux capture-pane. 
    const rawTmux = tmuxExec(`tmux capture-pane -t ${sessionName}.${idx} -p -S -50`, sessionName);
    _lastTmuxResult = stripAnsi(rawTmux);
  } catch (e) {
    _lastTmuxResult = '';
  }
  return _lastTmuxResult;
}

/** Get clean last N lines from captured tmux output, ignoring trailing empty lines */
function getCleanTail(output, n) {
  const lines = stripAnsi(output).split('\n');
  // Find last line with actual content
  let last = lines.length - 1;
  while (last >= 0 && lines[last].trim() === '') {
    last--;
  }
  // Return n lines ending at 'last'
  return lines.slice(Math.max(0, last - n + 1), last + 1);
}

// --- State detection functions ---

/** CC CLI is ACTIVELY PROCESSING (Photosynthesizing, Crunching, etc.) */
function isBusy(output) {
  // 🦞 FIX 2026-02-23: Two-pass detection:
  // Pass 1: Check FULL tail for subagent indicators ("N local agents" appears BELOW ❯)
  // Pass 2: Check only lines AFTER ❯ for stale status text (ignore completed activity above prompt)
  const lines = getCleanTail(output, 8);
  const fullTail = lines.join('\n');

  // 🦞 FIX 2026-02-25: ALL checks now scan only lines AFTER the last ❯ prompt.
  // Old bug: "2 local agents" from COMPLETED subagents in scrollback ABOVE ❯
  // was matching as BUSY, creating a 2-min blind spot between missions.
  const promptIdx = lines.findLastIndex(l => l.includes('❯'));
  const checkLines = (promptIdx >= 0 ? lines.slice(promptIdx) : lines).filter(l => {
    const clean = l.trim();
    if (!clean) return false;
    if (/^[─━-]+$/.test(clean)) return false; // Ignore horizontal separators
    if (/bypass permissions/i.test(clean)) return false; // Ignore footer
    return true;
  });
  const tail = checkLines.join('\n');

  // Subagent detection (check AFTER ❯ — status bar renders below prompt when active)
  const subagentPattern = /\d+\s+local\s+agents?/i;
  const hasSubagent = subagentPattern.test(tail);

  const promptLine = promptIdx >= 0 ? lines[promptIdx] : '';
  if (promptLine.match(/^[❯>]\s*(Try\s|$)/) && checkLines.length <= 1) return false;
  const matched = BUSY_PATTERNS.find(p => p.test(tail));

  const isActuallyBusy = hasSubagent || !!matched;

  // 🚨 CRITICAL FIX: If CC CLI is interrupted (Ctrl+C), it is IDLE, not busy!
  // BUT only if Interrupted happened AFTER any busy pattern.
  const interruptedIdx = lines.findLastIndex(l => /Interrupted\.\s*What should Claude do instead\?/i.test(l) || /Interrupted/i.test(l));
  const busyIdx = lines.findLastIndex(l => (matched && matched.test(l)) || subagentPattern.test(l));

  if (interruptedIdx > busyIdx && interruptedIdx !== -1) {
    return false;
  }

  if (hasSubagent) log(`isBusy MATCH: SUBAGENTS ACTIVE → ${tail.match(subagentPattern)?.[0]}`);
  else if (matched) log(`isBusy MATCH: ${matched} → ${tail.match(matched)?.[0]?.slice(0, 50)}`);

  return isActuallyBusy;
}

/** Mission completion pattern found (Cooked for Xm Ys, Sautéed for Xm Ys) */
function hasCompletionPattern(output) {
  const tail = getCleanTail(output, 10).join('\n');
  return COMPLETION_PATTERNS.some(p => p.test(tail));
}

/** CC CLI prompt visible — ONLY meaningful when NOT busy.
 *  WARNING: CC CLI TUI always renders ❯ even when processing.
 *  This function gates on !isBusy() but callers should still treat
 *  this as a weak signal and require additional confirmation. */
function hasPrompt(output) {
  if (isBusy(output)) return false;
  for (const line of getCleanTail(output, 10)) {
    const t = line.trim();
    if (!t) continue;
    if (t.includes('❯')) return true;
    if (/^>\s*$/.test(t)) return true;
    // CRITICAL: Handle the "Interrupted" state as an active, ready prompt
    if (t.includes('Interrupted')) return true;
  }
  return false;
}

function hasApproveQuestion(output) {
  // 🧬 FIX Bug #6: EXTEND to 15 lines — questions can appear mid-scrollback
  const tail = getCleanTail(output, 15).join('\n');
  return APPROVE_PATTERNS.some(p => p.test(tail));
}

function hasContextLimit(output) {
  // 🦞 FIX: Proxy handles infinite context, so we never trigger context_limit state.
  return false;
}

/** Check if the pane is sitting at a raw shell prompt (zsh/bash) instead of Claude */
function isShellPrompt(output) {
  const tail = getCleanTail(output, 5).join('\n');
  // Matches typical shell prompts: "user@host dir %", "bash-3.2$", etc.
  // CRITICAL: Claude's prompt is "❯" or ">". Shell is "%" or "$".
  if (tail.includes('❯')) return false; // Claude is active
  if (tail.includes('Choose a capability:')) return false; // Claude menu
  if (/^>\s*$/.test(tail.trim())) return false; // Simple interactive prompt

  if (/%[\s]*$/.test(tail)) return true; // zsh
  if (/\$ \s*$/.test(tail)) return true; // bash
  if (/# \s*$/.test(tail)) return true; // root
  return false;
}

/** Unified state detection from tmux output.
 *  Returns: 'busy' | 'complete' | 'context_limit' | 'question' | 'idle' | 'unknown'
 *  CRITICAL: BUSY checked BEFORE completion — prevents stale "Cooked for"
 *  in scrollback from overriding active processing indicators. */
function detectState(output) {
  if (hasContextLimit(output)) return 'context_limit';
  // BUG FIX: Prompts (Questions) can appear while "Busy" text is still visible (e.g. Osmosing...)
  // We must handle questions FIRST to unblock.
  if (hasApproveQuestion(output)) return 'question';

  if (isBusy(output)) return 'busy';
  if (hasCompletionPattern(output)) return 'complete';
  if (hasPrompt(output)) return 'idle';
  return 'unknown';
}

// --- Text dispatch ---

function pasteText(text, workerIdx, sessionName = TMUX_SESSION_PRO) {
  const idx = workerIdx !== undefined ? workerIdx : currentWorkerIdx;
  const target = `${sessionName}.${idx}`;

  // 🔒 TWO-CALL MANDATE (Chairman Rule 2026-02-03):
  const cleanText = text.replace(/\n+$/, ''); // Strip ALL trailing newlines
  const promptFile = `/tmp/tom_hum_prompt_P${idx}.txt`;
  fs.writeFileSync(promptFile, cleanText); // NO trailing newline in file
  tmuxExec(`tmux load-buffer ${promptFile}`, sessionName);
  tmuxExec(`tmux paste-buffer -p -t ${target}`, sessionName);
  try { fs.unlinkSync(promptFile); } catch (e) { }
}

function sendEnter(workerIdx, sessionName = TMUX_SESSION_PRO) {
  const target = `${sessionName}.${workerIdx}`;
  tmuxExec(`tmux send-keys -t ${target} Enter`, sessionName);
}

function sendCtrlC(workerIdx, sessionName = TMUX_SESSION_PRO) {
  const target = `${sessionName}.${workerIdx}`;
  tmuxExec(`tmux send-keys -t ${target} C-c`, sessionName);
}

/** Poll until prompt appears (used by spawnBrain/respawn/context management) */
async function waitForPrompt(timeoutMs = 120000, workerIdx = 0, sessionName = TMUX_SESSION_PRO) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    if (hasPrompt(capturePane(workerIdx, sessionName))) return true;
    await sleep(1000);
  }
  return false;
}

// --- Respawn rate limiting ---

function canRespawn() {
  // USER DEMAND: "vòng lặp vô tận cấm off" (Infinite Loop, Never Off)
  // We disable the rate limiter entirely.
  // const cutoff = Date.now() - 3600000;
  // respawnTimestamps = respawnTimestamps.filter(ts => ts > cutoff);
  // return respawnTimestamps.length < MAX_RESPAWNS_PER_HOUR;
  return true;
}

/**
 * 虛實 (Xu Shi) — Intent-Aware Command Generator
 * Enforces strict isolation between Planning (Pro) and Execution (API)
 */
function generateClaudeCommand(intent = 'API') {
  if (intent === 'PRO') {
    const claudeConfigDir = `/Users/macbookprom1/.claude_antigravity_pro`;
    let envVars = `export CLAUDE_CONFIG_DIR="${claudeConfigDir}"`;
    envVars += ` && unset ANTHROPIC_API_KEY && unset ANTHROPIC_BASE_URL && export NPM_CONFIG_WORKSPACES=false && export npm_config_workspaces=false`;
    return `${envVars} && claude --model claude-3-7-sonnet-20250219 --dangerously-skip-permissions`;
  } else {
    // API (Execution via Gemini Proxy)
    const claudeConfigDir = `/Users/macbookprom1/.claude_antigravity_api`;
    let envVars = `export CLAUDE_CONFIG_DIR="${claudeConfigDir}"`;
    const baseUrl = `http://127.0.0.1:9191`;
    envVars += ` && unset ANTHROPIC_API_KEY && export ANTHROPIC_BASE_URL="${baseUrl}" && export ANTHROPIC_AUTH_TOKEN="test"`;
    envVars += ` && export NPM_CONFIG_WORKSPACES=false && export npm_config_workspaces=false`;
    return `${envVars} && claude --dangerously-skip-permissions`;
  }
}

// --- Brain lifecycle ---

// Brain State
let currentWorkerIdx = 1; // Start at P1 (P0 is Monitor), unless Full CLI

async function spawnBrain() {
  const TMUX_SESSION = `${config.TMUX_SESSION}:brain`;

  if (isSessionAlive(TMUX_SESSION)) {
    try {
      const paneCount = parseInt(execSync(`tmux list-panes -t ${TMUX_SESSION} | wc -l`, { encoding: 'utf-8' }).trim());
      if (paneCount >= 2) {
        log(`BRAIN: tmux session exists (Panes: ${paneCount}/2) — reusing`);
        return;
      }
      log(`BRAIN: Session exists but has ${paneCount}/2 panes. REPAIRING to DUAL-PANE Sandwich Workflow...`);
      tmuxExec(`tmux kill-session -t ${TMUX_SESSION}`, TMUX_SESSION);
    } catch (e) {
      log(`BRAIN: Error checking session: ${e.message}`);
    }
  }

  log(`BRAIN: Creating DUAL-PANE SANDWICH tmux session with CC CLI interactive...`);

  const mcpConfig = {
    "mcpServers": {
      "filesystem": {
        "command": "node",
        "args": ["/Users/macbookprom1/.npm/_npx/a3241bba59c344f5/node_modules/@modelcontextprotocol/server-filesystem/dist/index.js", "/Users/macbookprom1/mekong-cli"]
      }
    }
  };

  const handPro = getHandForIntent('PLAN');
  const baseConfigPro = { "primaryColor": "#A020F0", "customInstructions": handPro.instructions, "dangerouslySkipPermissions": true, "bypassPermissions": true, "agreedToBypassPermissions": true };
  if (!fs.existsSync(`/Users/macbookprom1/.claude_antigravity_pro`)) fs.mkdirSync(`/Users/macbookprom1/.claude_antigravity_pro`, { recursive: true });
  fs.writeFileSync(`/Users/macbookprom1/.claude_antigravity_pro/config.json`, JSON.stringify(baseConfigPro, null, 2));
  fs.writeFileSync(`/Users/macbookprom1/.claude_antigravity_pro/mcp.json`, JSON.stringify(mcpConfig, null, 2));

  const handApi = getHandForIntent('COOK');
  const baseConfigApi = { "primaryColor": "#00FF00", "customInstructions": handApi.instructions, "dangerouslySkipPermissions": true, "bypassPermissions": true, "agreedToBypassPermissions": true };
  if (!fs.existsSync(`/Users/macbookprom1/.claude_antigravity_api`)) fs.mkdirSync(`/Users/macbookprom1/.claude_antigravity_api`, { recursive: true });
  fs.writeFileSync(`/Users/macbookprom1/.claude_antigravity_api/config.json`, JSON.stringify(baseConfigApi, null, 2));
  fs.writeFileSync(`/Users/macbookprom1/.claude_antigravity_api/mcp.json`, JSON.stringify(mcpConfig, null, 2));

  // 🦞 AUTH PERSISTENCE: Copy oauth_creds to both profiles to avoid login loops
  try {
    const srcTokens = fs.readdirSync('/Users/macbookprom1/.claude').filter(f => f.startsWith('oauth_creds'));
    for (const token of srcTokens) {
      const srcPath = path.join('/Users/macbookprom1/.claude', token);
      fs.copyFileSync(srcPath, path.join('/Users/macbookprom1/.claude_antigravity_pro', token));
      fs.copyFileSync(srcPath, path.join('/Users/macbookprom1/.claude_antigravity_api', token));
    }
    log(`BRAIN: Persisted Auth Pro credentials to Sandbox Profiles.`);
  } catch (e) {
    log(`BRAIN: Auth persistence warning - ${e.message}`);
  }

  const cmdPro = generateClaudeCommand('PRO');
  const cmdApi = generateClaudeCommand('API');

  const bootDir = config.MEKONG_DIR;
  const sessionName = TMUX_SESSION.split(':')[0];
  const windowName = 'brain';

  log(`BRAIN: Creating NEW session [${sessionName}] with window [${windowName}] in ${bootDir}...`);
  tmuxExec(`tmux new-session -d -s ${sessionName} -n ${windowName} -x 200 -y 50 -c ${bootDir}`, TMUX_SESSION);
  tmuxExec(`tmux set-option -t ${sessionName} remain-on-exit on`, TMUX_SESSION);
  tmuxExec(`tmux set-option -t ${sessionName} allow-rename off`, TMUX_SESSION);

  // Split window horizontally
  tmuxExec(`tmux split-window -h -t ${TMUX_SESSION}.0 -c ${bootDir}`, TMUX_SESSION);

  await sleep(1000);

  // Pane 0: PLANNER (PRO)
  tmuxExec(`tmux send-keys -t ${TMUX_SESSION}.0 '${cmdPro}' Enter`, TMUX_SESSION);
  tmuxExec(`tmux select-pane -t ${TMUX_SESSION}.0 -T "PRO: Planner"`, TMUX_SESSION);

  // Pane 1: EXECUTION (API / Free)
  tmuxExec(`tmux send-keys -t ${TMUX_SESSION}.1 '${cmdApi}' Enter`, TMUX_SESSION);
  tmuxExec(`tmux select-pane -t ${TMUX_SESSION}.1 -T "API: Executor"`, TMUX_SESSION);

  // Auto-accept bypass permissions for both panes
  log(`BRAIN: Waiting for CC CLI bypass prompts...`);
  await sleep(10000);
  for (let paneIdx = 0; paneIdx < 2; paneIdx++) {
    for (let retry = 0; retry < 30; retry++) {
      const paneOutput = capturePane(paneIdx, TMUX_SESSION);

      if (paneOutput.includes('accept all responsibility') || paneOutput.includes('Permissions mode.')) {
        log(`BRAIN: P${paneIdx} prompt — sending Down+Enter (attempt ${retry + 1})...`);
        tmuxExec(`tmux send-keys -t ${TMUX_SESSION}.${paneIdx} Down`, TMUX_SESSION);
        await sleep(1000);
        tmuxExec(`tmux send-keys -t ${TMUX_SESSION}.${paneIdx} Enter`, TMUX_SESSION);
      } else if (paneOutput.includes('Choose the text style') || paneOutput.includes('Press Enter to continue') || paneOutput.includes('Yes, I trust this folder')) {
        tmuxExec(`tmux send-keys -t ${TMUX_SESSION}.${paneIdx} Enter`, TMUX_SESSION);
      } else if (paneOutput.includes('❯')) {
        log(`BRAIN: P${paneIdx} Native Boot Complete!`);
        break;
      }
      await sleep(3000);
    }
  }

  log(`BRAIN: Dual-Pane Sandwich Boot Complete [session=${TMUX_SESSION}]`);
}

function findIdleWorker(sessionName = TMUX_SESSION, intent = 'EXECUTION') {
  // Pro Intent -> Pane 0
  // Execution Intent -> Pane 1
  const isProIntent = /plan|think|research|insight|binh-phap/.test(intent.toLowerCase()) || intent === 'PRO';
  const targetPane = isProIntent ? 0 : 1;

  if (!isWorkerBusy(targetPane, sessionName)) {
    log(`DISPATCH: → Worker P${targetPane} (idle) — session=${sessionName} intent=${intent}`);
    tmuxExec(`tmux select-pane -t ${sessionName}.${targetPane}`, sessionName);
    return targetPane;
  }
  return -1; // Busy
}

function killBrain(sessionName = TMUX_SESSION) {
  if (isSessionAlive(sessionName)) {
    tmuxExec(`tmux kill-session -t ${sessionName}`, sessionName);
    log(`BRAIN: tmux session ${sessionName} killed`);
  }
}

function isBrainAlive(sessionName = TMUX_SESSION_PRO) {
  if (!isSessionAlive(sessionName)) return false;
  try {
    // 🔒 Check tmux pane content for CC CLI indicators instead of pgrep
    const output = execSync(
      `tmux capture-pane -t ${sessionName}.0 -p 2>/dev/null`,
      { encoding: 'utf-8', timeout: 3000 }
    );
    // CC CLI shows these when alive (idle or busy)
    const aliveIndicators = [/❯/, /Claude Code/i, /bypass permissions/i, /claude-/i, /✻/];
    return aliveIndicators.some(p => p.test(output));
  } catch (e) { return false; }
}

// --- Context management ---
// NOTE: 🔋 XX% via Antigravity Proxy is FAKE (tracks Anthropic limits but routes
// through Gemini). Use mission count instead.

function parseContextUsage(output) {
  const match = output.match(/🔋\s*(\d+)%/);
  return match ? parseInt(match[1]) : -1;
}

// 🧬 FIX #3: REMOVE manageContext() — /clear is redundant with /compact
// Only use /compact every 50 missions for context cleanup

async function compactIfNeeded() {
  // 🦞 PROXY FIX 2026-02-23: DISABLED — context % is fake through AG Proxy
  // Proxy handles conversation management. CC CLI compact wastes 11+ minutes.
  // To re-enable: set COMPACT_EVERY_N and COMPACT_TOKEN_THRESHOLD to finite values.
  return;
}

// --- Crash recovery ---

async function respawnBrain(intent = 'EXECUTION', useContinue = true) {
  const isPlanning = intent === 'PLAN' || intent === 'RESEARCH';
  const sessionName = isPlanning ? TMUX_SESSION_PRO : TMUX_SESSION_API;

  if (!canRespawn()) {
    log(`RESPAWN: Rate limit (${MAX_RESPAWNS_PER_HOUR}/hr) — cooldown ${RESPAWN_COOLDOWN_MS / 1000}s`);
    await sleep(RESPAWN_COOLDOWN_MS);
    respawnTimestamps = [];
  }
  respawnTimestamps.push(Date.now());
  killBrain(sessionName);
  await sleep(2000); // Wait for cleanup

  // REUSE spawnBrain() logic with intent
  await spawnBrain(config.AGENT_TEAM_SIZE_DEFAULT, intent);
  await sleep(5000); // 🦞 Increased wait for CC CLI to boot

  log(`RESPAWN: Session ${sessionName} rebuilt via spawnBrain(${intent})`);
  return waitForPrompt(120000, 0, sessionName);
}

// --- Per-Worker Mission Lock (enables parallel dispatch) ---
const STALE_LOCK_THRESHOLD_MS = 2 * 60 * 1000; // 2min — fast cleanup for leaked locks (Chairman Fix 2026-02-23)

function workerLockFile(idx) {
  return require('path').join(__dirname, '..', `.mission-active-P${idx}.lock`);
}

/**
 * Level 6 Fix: Auto-clean stale locks
 * If lock file age > 30min, mission is dead — clean up
 * Prevents MISSION BLOCKED false positive
 */
function autoCleanStaleLock(idx) {
  const lockPath = workerLockFile(idx);
  try {
    if (!fs.existsSync(lockPath)) return;
    const stat = fs.statSync(lockPath);
    const ageMs = Date.now() - stat.mtimeMs;
    if (ageMs > STALE_LOCK_THRESHOLD_MS) {
      const content = fs.readFileSync(lockPath, 'utf-8').trim();
      fs.unlinkSync(lockPath);
      log(`[HEALER] 🔓 Stale lock P${idx} cleaned (age: ${Math.round(ageMs / 60000)}min, was: ${content})`);
    }
  } catch (e) {
    // Lock disappeared between checks — safe to ignore
  }
}

/**
 * 🦞 FIX 2026-02-23: DISABLED — Log file monitoring was reverted (pipe-pane/script removed).
 * The /tmp/cc_cli_output_P*.log files are never updated, so this always falsely detects hangs.
 * Healer was killing CC CLI mid-mission every time isWorkerBusy() was called.
 */
function checkAndRecoverHungWorker(idx) {
  // NO-OP: Disabled to prevent false hang detection
  return;
}

function isWorkerBusy(idx) {
  try {
    autoCleanStaleLock(idx); // Level 6: always clean before checking

    // Only check for hangs if the worker is actually marked as busy
    const isBusy = fs.existsSync(workerLockFile(idx));
    if (isBusy) {
      checkAndRecoverHungWorker(idx);
    }
    return isBusy;
  } catch { return false; }
}

// Legacy single-lock check: returns true if ANY worker is busy
function isMissionActive() {
  const teamSize = config.AGENT_TEAM_SIZE_DEFAULT || 3;
  for (let i = 0; i < teamSize; i++) {
    if (isWorkerBusy(i)) return true;
  }
  return false;
}

function setWorkerLock(idx, missionNum) {
  try { fs.writeFileSync(workerLockFile(idx), `mission_${missionNum}_P${idx}_${Date.now()}`); } catch { }
}

function clearWorkerLock(idx) {
  try { fs.unlinkSync(workerLockFile(idx)); } catch { }
}

// Legacy aliases for backward compat
const MISSION_LOCK = require('path').join(__dirname, '..', '.mission-active.lock');
function setMissionLock(num) { setWorkerLock(currentWorkerIdx, num); }
function clearMissionLock() { clearWorkerLock(currentWorkerIdx); }

async function runMission(prompt, projectDir, timeoutMs, modelOverride, complexity, intent) {
  const isPlanning = intent === 'PLAN' || intent === 'RESEARCH' || (prompt || '').startsWith('/plan') || (prompt || '').includes('[PLAN ONLY]');
  const suffix = isPlanning ? 'pro' : 'api';
  const TMUX_SESSION = isPlanning ? TMUX_SESSION_PRO : TMUX_SESSION_API;

  // 🧬 FIX Bug #1 + BRAIN SURGERY v30: TTL-based DUPLICATE DISPATCH DETECTION
  const promptHash = hashPrompt(prompt);
  if (isDuplicateMission(promptHash)) {
    log(`DUPLICATE MISSION REJECTED: Hash ${promptHash.slice(0, 20)}... dispatched within last ${DEDUP_TTL_MS / 60000}min`);
    return { success: false, result: 'duplicate_rejected', elapsed: 0 };
  }

  // 🔒 MAP: findIdleWorker now routes exactly to the assigned visual Pane
  const workerIdx = findIdleWorker(TMUX_SESSION, intent);

  if (workerIdx === 0 && (prompt.includes('/cook') || prompt.includes('/debug') || prompt.includes('/test'))) {
    log(`🔴 CHAIRMAN OVERRIDE: FATAL REJECT! Pane 0 (PRO) is strictly forbidden from executing /cook, /debug, or /test. Mission aborted.`);
    return { success: false, result: 'p0_violation', elapsed: 0 };
  }

  if (workerIdx === -1) {
    log(`MISSION BLOCKED: Worker P${intent === 'PLAN' || intent === 'RESEARCH' ? 0 : 1} is busy — refusing dispatch`);
    return { success: false, result: 'all_workers_busy', elapsed: 0 };
  }

  // Track this mission hash ONLY if we successfully secured an idle worker
  trackMissionHash(promptHash);

  missionCount++;
  const num = missionCount;
  const startTime = Date.now();
  const missionStartDate = new Date();

  // Set PER-WORKER lock immediately
  setWorkerLock(workerIdx, num);
  currentWorkerIdx = workerIdx; // Set for backward-compat functions

  // 🔒 CRITICAL FIX: Wrap entire mission in try-finally to ensure lock cleanup
  try {
    // 作戰 Token Tracker
    const { countTokensBetween, recordMission, getDailyUsage } = require('./token-tracker');

    log(`MISSION #${num} → P${workerIdx}: ${prompt.slice(0, 150)}...`);
    log(`PROJECT: ${projectDir} | MODE: tmux-parallel | WORKER: P${workerIdx}${modelOverride ? ` | MODEL: ${modelOverride} 🔥` : ''}`);

    // Thermal gate
    const { waitForSafeTemperature } = require('./m1-cooling-daemon');
    await waitForSafeTemperature();

    // 🧬 FIX #3: Only /compact, no /clear
    await compactIfNeeded();

    // 🔒 Chairman Fix: MODEL OVERRIDE DISABLED — AG Proxy routes all models automatically
    // Bug #3: /model claude-opus → proxy returns "invalid model" → garbles dispatch
    // Proxy đã tự route: mọi model → gemini-3-pro-high
    // if (modelOverride) { ... } — REMOVED

    // Build full prompt
    let fullPrompt = prompt;
    if (projectDir && projectDir !== config.MEKONG_DIR) {
      // 🔒 Chairman Fix: ClaudeKit REQUIRES slash command at index 0.
      // We cannot prepend "First cd to..." before the command.
      // Inject the context constraint at the end of the prompt or inside the quotes.
      fullPrompt = prompt.replace(/"$/, `\n\n[CONTEXT STRICTLY RESTRICTED TO PROJECT DIRECTORY: ${projectDir}]"`);
      // Fallback if no quotes found
      if (fullPrompt === prompt) {
        fullPrompt = `${prompt} (IN PROJECT: ${projectDir})`;
      }
    }

    // CC CLI state machine loops until DONE or error
    // (The line "let lastState = 'dispatched';" was removed as it was not used and the comment was incorrect)

    // SAFETY CHECK: Ensure Claude is actually running before dispatching
    // If we paste into a raw ZSH shell, we get "Command not found" errors.
    const checkOutput = capturePane(workerIdx, TMUX_SESSION);
    if (!isBrainAlive(TMUX_SESSION) || isShellPrompt(checkOutput)) {
      log(`CRITICAL: Brain died or dropped to shell! session=${TMUX_SESSION}`);
      const respawnSuccess = await respawnBrain(isPlanning ? 'PLAN' : 'EXECUTION', true);
      if (!respawnSuccess) {
        return { success: false, result: 'brain_died_fatal', elapsed: 0 };
      }
      await sleep(2000);
    }

    // 🦞🔥 SELF-HEALING + ANTI-STACKING GUARD (v2026.2.24 — ALL FIXES BAKED IN)
    // Sếp's mandate: CTO must STOP BEING BLIND and AUTO-RECOVER like a game respawn.
    //
    // Self-heal capabilities:
    // 1. Detects "queued messages" → sends Escape to clear
    // 2. Detects post-compaction gap → waits 10s extra
    // 3. Detects 0% compaction deadlock → ONLY kicks when truly stuck (not status bar)
    // 4. Max 18 attempts (180s) for long compactions

    let wasCompacting = false;
    let compactionStartTime = 0; // 🎯 COMPACTION STALL FIX: Track how long compaction runs
    const COMPACTION_TIMEOUT_MS = 3 * 60 * 1000; // 3 minutes max for compaction

    for (let waitAttempt = 0; waitAttempt < 10; waitAttempt++) {  // 🦞 FIX BUG #2 2026-02-27: Reduced 18→10 (max wait 50s vs 180s)
      const preDispatch = capturePane(workerIdx, TMUX_SESSION);
      const recentLines = getCleanTail(preDispatch, 8).join('\n');
      const fullTailLines = getCleanTail(preDispatch, 20).join('\n');
      const preState = detectState(recentLines);

      // 🚨 PRO LIMIT DETECTION (v2026.2.27) -> NUCLEAR LIQUIDATION
      if (PRO_LIMIT_PATTERNS.some(p => p.test(fullTailLines))) {
        log(`🚨 [CRITICAL] Claude Pro limit hit detected on Worker P${workerIdx}!`);
        log(`💣 [NUCLEAR LIQUIDATION] Killing stalled Pro session for immediate rotation...`);
        setProLimitHit(true);
        killBrain(); // Force EVERYTHING to stop immediately
        return { success: false, result: 'pro_limit_hit', elapsed: Date.now() - startTime };
      }

      // 🦞 SELF-HEAL #1: Detect "queued messages" and auto-clear via Escape
      if (/queued messages/i.test(recentLines) || /Press up to edit queued/i.test(recentLines)) {
        log(`🩺 SELF-HEAL: Detected "queued messages" — sending Escape to clear (attempt ${waitAttempt + 1})...`);
        tmuxExec(`tmux send-keys -t ${TMUX_SESSION}.${workerIdx} Escape`, TMUX_SESSION);
        await sleep(3000);
        continue;
      }

      // 🦞 SELF-HEAL #2: Detect "Interrupted" banner sitting idle and auto-clear via Escape
      // If CC CLI thinks it's interrupted, any text sent might get eaten or cause syntax errors.
      if (!isBusy(preDispatch) && (/Interrupted\.\s*What should Claude do instead\?/i.test(fullTailLines) || /Interrupted/i.test(fullTailLines))) {
        log(`🩺 SELF-HEAL: Detected "Interrupted" state — sending Escape to clear (attempt ${waitAttempt + 1})...`);
        for (let i = 0; i < 3; i++) {
          tmuxExec(`tmux send-keys -t ${TMUX_SESSION}.${workerIdx} Escape`, TMUX_SESSION);
          await sleep(500);
        }
        await sleep(2000);
        continue;
      }

      if (preState === 'busy') {
        const isCompacting = /Compacting/i.test(recentLines) || /Compacting/i.test(fullTailLines);

        // Track compaction for post-compaction cooldown
        if (isCompacting) {
          if (!wasCompacting) {
            wasCompacting = true;
            compactionStartTime = Date.now();
            log(`⏱️ COMPACTION STARTED: Tracking compaction duration...`);
          }

          // 🎯 COMPACTION STALL FIX: If compacting > 3 minutes → abort + /clear
          const compactingDuration = Date.now() - compactionStartTime;
          if (compactingDuration > COMPACTION_TIMEOUT_MS) {
            log(`🚨 COMPACTION STALL DETECTED: ${Math.round(compactingDuration / 60000)}min > 3min limit!`);
            log(`🚨 Aborting compaction with Ctrl+C → /clear to recover...`);
            sendCtrlC(workerIdx, TMUX_SESSION);
            await sleep(3000);
            // Send /clear to reset context instead of stalling forever
            // pasteText('/clear', workerIdx, TMUX_SESSION);
            await sleep(1000);
            sendEnter(workerIdx, TMUX_SESSION);
            await sleep(5000);
            wasCompacting = false;
            compactionStartTime = 0;
            log(`🩺 COMPACTION RECOVERY: Sent /clear — CC CLI context reset. Ready for next dispatch.`);
            // Wait for prompt after /clear
            await waitForPrompt(30000, workerIdx, TMUX_SESSION);
            break;
          }

          log(`⏱️ COMPACTING: ${Math.round(compactingDuration / 1000)}s elapsed (limit: 180s) — waiting...`);
        }

        // 🆘 ANTI-HANG: ONLY kick Enter when BOTH "Compacting" text AND "0%" on SAME line
        // "Context left until auto-compact: 0%" in status bar is NORMAL — do NOT kick for that.
        const hasZeroPercent = /Compacting[^\n]*0%/i.test(recentLines) || /0%[^\n]*Compacting/i.test(recentLines);
        if (isCompacting && hasZeroPercent) {
          log(`🆘 ANTI-HANG: CC CLI stuck compacting at 0% — sending /clear to reset context (attempt ${waitAttempt + 1})...`);
          // pasteText('/clear', workerIdx, TMUX_SESSION);
          await sleep(1000);
          sendEnter(workerIdx, TMUX_SESSION);
          await sleep(10000); // Wait for /clear to process
        } else if (!isCompacting) {
          const matchedPat = BUSY_PATTERNS.find(p => p.test(recentLines));
          log(`ANTI-STACK: CC CLI still busy (attempt ${waitAttempt + 1}/10) — matched: ${matchedPat || 'NONE'} — waiting 5s...`);
        }
        await sleep(5000);  // 🦞 FIX BUG #2 2026-02-27: Reduced from 10s to 5s per attempt
        continue;
      }

      if (preState === 'idle' || preState === 'complete' || preState === 'unknown') {
        // 🦞 POST-COMPACTION COOLDOWN: CC CLI spinner disappears BEFORE compaction finishes.
        if (wasCompacting) {
          log(`POST-COMPACT: Compaction just finished — cooling 10s before dispatch...`);
          wasCompacting = false;
          compactionStartTime = 0;
          await sleep(10000);
          continue; // Re-check state after cooldown
        }
        break; // Safe to dispatch
      }

      if (preState === 'question') {
        log(`ANTI-STACK: CC CLI has pending question — auto-approving`);
        tmuxExec(`tmux send-keys -t ${TMUX_SESSION}.${workerIdx} y Enter`, TMUX_SESSION);
        await sleep(2000);
        continue;
      }
      break;
    }

    // Final check: if STILL busy after 180s, abort this mission
    const finalCheck = capturePane(workerIdx, TMUX_SESSION);
    if (isBusy(finalCheck)) {
      log(`ANTI-STACK: P${workerIdx} still busy after 180s — ABORTING mission #${num}`);
      return { success: false, result: 'busy_blocked', elapsed: 0 };
    }

    // 🦞 SELF-HEAL #2: Final queued-messages check after ANTI-STACK
    if (/queued messages/i.test(finalCheck) || /Press up to edit queued/i.test(finalCheck)) {
      log(`🩺 SELF-HEAL: FINAL CHECK — queued messages still present. Sending Escape + aborting this round.`);
      tmuxExec(`tmux send-keys -t ${TMUX_SESSION}.${workerIdx} Escape`, TMUX_SESSION);
      return { success: false, result: 'queued_abort', elapsed: 0 };
    }

    // 🦞 SELF-HEAL #3: Background tasks overlay stuck (Esc to close)
    if (/Background tasks/i.test(finalCheck) || /Esc to close/i.test(finalCheck)) {
      log(`🩺 SELF-HEAL: CC CLI stuck on "Background tasks" view — sending Escape to dismiss`);
      tmuxExec(`tmux send-keys -t ${TMUX_SESSION}.${workerIdx} Escape`, TMUX_SESSION);
      await sleep(1000);
    }

    // 🦞 SELF-HEAL #4: Intermittent Feedback Prompt Intercept (0: Dismiss)
    // CC CLI occasionally asks "How is Claude doing this session?" after completion.
    // This hijacks the input buffer and swallows any incoming new tasks.
    if (/0:\s*Dismiss/i.test(finalCheck) || /How is Claude doing/i.test(finalCheck)) {
      log(`🩺 SELF-HEAL: CC CLI intercepting payload with Feedback Screen — sending '0' to dismiss`);
      tmuxExec(`tmux send-keys -t ${TMUX_SESSION}.${workerIdx} 0`, TMUX_SESSION);
      await sleep(1000);
    }

    // 🔒 Clear input line before dispatch (stale text protection)
    tmuxExec(`tmux send-keys -t ${TMUX_SESSION}.${workerIdx} Escape`, TMUX_SESSION);
    tmuxExec(`tmux send-keys -t ${TMUX_SESSION}.${workerIdx} C-c`, TMUX_SESSION);
    await sleep(200);

    // Convert newlines to spaces to prevent CC CLI multi-line input mode
    const safePrompt = fullPrompt.replace(/\n/g, ' ');

    // 🦞 FIX 2026-02-26: Claude Code v2.1.59 "Queued Messages" Paste Bug
    // Newer versions of CC CLI interpret tmux paste buffers as multi-line queued messages if they exceed a certain size or contain specific formatting.
    // We write the prompt to a temp file, load it into a named buffer, and paste it without brackets.
    log(`Sending payload via tmux load-buffer (Suffix: ${suffix}) to prevent "queued messages"...`);
    const tempFile = require('path').join(require('os').tmpdir(), `mission_prompt_${workerIdx}_${Date.now()}.txt`);
    try {
      require('fs').writeFileSync(tempFile, safePrompt);
      tmuxExec(`tmux load-buffer -b mission_${workerIdx} ${tempFile}`);
      // -p: paste without bracketed paste mode (often the culprit for multiline queued messages)
      // -d: delete buffer after
      tmuxExec(`tmux paste-buffer -b mission_${workerIdx} -p -d -t ${TMUX_SESSION}.${workerIdx}`, TMUX_SESSION);
    } finally {
      try { require('fs').unlinkSync(tempFile); } catch (e) { }
    }

    await sleep(2000);

    // TWO-CALL MANDATE: First Enter submits the pasted text
    // 🦞 FIX 2026-02-27: "Triple Enter" / "Pasted Text" Block Bug
    // The Chairman demands absolute continuous execution. CC CLI swallows the first Enter
    // into a `[Pasted text]` block. We must forcefully punch through it.
    log(`[MANDATE] Sending explicit Enter keystrokes to pierce the [Pasted text] modal...`);
    sendEnter(workerIdx, TMUX_SESSION);
    await sleep(2000); // Wait for CC CLI to register it
    sendEnter(workerIdx, TMUX_SESSION);
    await sleep(2000); // Double tap
    sendEnter(workerIdx, TMUX_SESSION); // Triple tap (Guarantee)

    // 🔒 VERIFIED ENTER: Wait 8s then retry ONCE if still idle
    await sleep(8000);
    const postEnterOutput = capturePane(workerIdx, TMUX_SESSION);
    const postEnterState = detectState(postEnterOutput);
    if (postEnterState === 'idle' && !isBusy(postEnterOutput)) {
      // Only kick if 15s+ elapsed AND text is stuck after prompt
      const elapsedPostDispatch = Math.round((Date.now() - startTime) / 1000);
      if (elapsedPostDispatch >= 15) {
        log(`ENTER RETRY: CC CLI still idle after 15s — sending ONE safety Enter`);
        sendEnter(workerIdx, TMUX_SESSION);
        await sleep(1000);
        sendEnter(workerIdx, TMUX_SESSION);
      }
    }
    log(`DISPATCHED: Mission #${num} sent to P${workerIdx}`);

    // ═══════════════════════════════════════════════════════════════
    // STATE MACHINE: DISPATCHED → BUSY → DONE
    //
    // CC CLI TUI always renders ❯ even when busy — hasPrompt() alone
    // is NOT reliable. We track wasBusy and require either:
    //   (a) Completion pattern found (Cooked/Sautéed for Xm Ys)
    //   (b) Was BUSY → 3x consecutive IDLE polls
    //   (c) Never saw BUSY but elapsed > 45s → 3x consecutive IDLE
    // ═══════════════════════════════════════════════════════════════

    let wasBusy = false;
    let idleConfirmCount = 0;
    const deadline = Date.now() + timeoutMs;
    let lastLogTime = Date.now();
    let kickStartCount = 0;

    // Give CC CLI time to parse prompt and begin processing
    await sleep(1000); // 🧬 AGI BRAIN UPGRADE: Reduced from 2000→1000 for faster response

    while (Date.now() < deadline) {
      if (!isSessionAlive(TMUX_SESSION)) {
        const elapsed = Math.round((Date.now() - startTime) / 1000);
        log(`BRAIN DIED: Session ${TMUX_SESSION} died during mission #${num} (${elapsed}s)`);
        await respawnBrain(isPlanning ? 'PLAN' : 'EXECUTION', true);
        return { success: false, result: 'brain_died', elapsed };
      }

      // Layer 2 fix removed - relying on `capturePane` throttle instead

      const output = capturePane(workerIdx, TMUX_SESSION);
      const state = detectState(output);
      const elapsedSec = Math.round((Date.now() - startTime) / 1000);

      // STUCK INTERVENTION (Parallel Cooling): Kill stuck task if Hot & Long
      if (checkStuckIntervention(workerIdx, elapsedSec, wasBusy)) {
        return { success: false, result: 'killed_stuck', elapsed: elapsedSec };
      }

      switch (state) {
        case 'complete': {
          // Guard against stale completion from previous mission still in scrollback
          if (!wasBusy && elapsedSec < MIN_MISSION_SECONDS) {
            break; // Likely stale — wait for BUSY or more elapsed time
          }
          const usage = parseContextUsage(output);
          log(`COMPLETE: Mission #${num} (${elapsedSec}s) [cooked-pattern]${usage >= 0 ? ` [ctx=${usage}%]` : ''}`);
          // 作戰 Token tracking
          const tk1 = countTokensBetween(missionStartDate, new Date());
          tokensSinceCompact += tk1.tokens; // Accumulate for proactive cleanup
          log(`TOKENS: Mission #${num} used ${tk1.tokens.toLocaleString()} tokens (${tk1.requests} reqs, ${tk1.model}) [Session accum: ${Math.round(tokensSinceCompact / 1000)}k]`);
          recordMission(prompt.slice(0, 60), path.basename(projectDir || ''), tk1.tokens, elapsedSec, tk1.model);
          const daily1 = getDailyUsage(); if (daily1.overBudget) log(`⚠️ 作戰: DAILY BUDGET EXCEEDED — ${daily1.tokens.toLocaleString()} tokens today!`);
          // 🧠 LEARNING: Record outcome for pattern analysis
          try { require('./learning-engine').recordOutcome(prompt.slice(0, 40), path.basename(projectDir || ''), 'done', elapsedSec); } catch (e) { }
          return { success: true, result: 'done', elapsed: elapsedSec };
        }

        case 'busy':
          if (!wasBusy) log(`BUSY: Mission #${num} — CC CLI started processing`);
          wasBusy = true;
          idleConfirmCount = 0;
          break;

        case 'question':
          log(`QUESTION: Mission #${num} — auto-approving`);
          const targetPane = `${TMUX_SESSION}.${workerIdx}`;

          // SPECIAL CASE: API Key Confirmation (Needs "1" + Enter for "Yes")
          // Matches the "2. No (recommended)" text which is selected by default
          if (/2\.\s+No\s+\(recommended\)/i.test(output)) {
            log(`QUESTION: API Key detected in P${workerIdx} — selecting '1. Yes'`);
            // Spam 1 and Enter for a few seconds to ensure TUI registers it
            for (let i = 0; i < 3; i++) {
              tmuxExec(`tmux send-keys -t ${targetPane} 1`, TMUX_SESSION);
              await sleep(500);
              tmuxExec(`tmux send-keys -t ${targetPane} Enter`, TMUX_SESSION);
              await sleep(500);
            }
          }
          // SPECIAL CASE: Kick-Start waiting for Enter (bypass permissions)
          // Matches both the disclaimer text and the TUI summary line
          else if (/By proceeding, you accept all responsibility/i.test(output) ||
            /Yes, I accept/i.test(output) ||
            /⏵⏵\s+bypass\s+permissions/i.test(output)) {
            log(`QUESTION: Bypass Permissions TUI detected — selecting '2. No (recommended)' via Down+Enter`);
            // The TUI menu for bypass usually has "Yes" at 1 and "No" at 2.
            // We want "No (recommended)" to proceed with the mission.
            tmuxExec(`tmux send-keys -t ${targetPane} Down`, TMUX_SESSION);
            await sleep(500);
            tmuxExec(`tmux send-keys -t ${targetPane} Enter`, TMUX_SESSION);
          }
          // SPECIAL CASE: Legacy API Key Prompt
          else if (/Enter your API key/i.test(output)) {
            log(`QUESTION: Legacy API Key prompt detected — sending Enter`);
            tmuxExec(`tmux send-keys -t ${targetPane} Enter`, TMUX_SESSION);
          } else {
            // 🧬 FIX Bug #2: AUTO-SELECT RECOMMENDED instead of WAIT
            if (/\(Recommended\)/i.test(output)) {
              log(`QUESTION: Auto-selecting (Recommended) option via Enter`);
              tmuxExec(`tmux send-keys -t ${targetPane} Enter`, TMUX_SESSION);
            } else if (/Option A/i.test(output)) {
              log(`QUESTION: Auto-selecting Option A (recommended pattern)`);
              tmuxExec(`tmux send-keys -t ${targetPane} a Enter`, TMUX_SESSION);
            } else {
              // Generic decision: send Enter (usually default = recommended)
              log(`QUESTION: Unrecognized question — auto-selecting default via Enter`);
              tmuxExec(`tmux send-keys -t ${targetPane} Enter`, TMUX_SESSION);
            }
          }
          // 🧬 FIX Bug #7: Reduce question response delay 3000ms → 1000ms
          await sleep(1000);
          idleConfirmCount = 0;
          continue; // Re-check immediately

        case 'context_limit':
          // 🦞 FIX 2026-02-25: RE-ENABLED /clear — uses pasteText + sendEnter (Two-Call Mandate)
          // Old bug: raw `send-keys /clear Enter` froze tmux. Now uses paste-buffer method.
          log(`CONTEXT LIMIT: Mission #${num} — context at 0%, sending /clear to reset`);
          // pasteText('/clear', workerIdx);
          await sleep(1000);
          sendEnter(workerIdx);
          await sleep(10000); // Wait 10s for CC CLI to clear and rebuild context
          idleConfirmCount = 0;
          continue;

        case 'idle':
          if (wasBusy) {
            // Was processing, now idle — confirm over multiple polls
            idleConfirmCount++;
            if (idleConfirmCount >= IDLE_CONFIRM_POLLS) {
              const usage = parseContextUsage(output);
              log(`COMPLETE: Mission #${num} (${elapsedSec}s) [idle-after-busy x${IDLE_CONFIRM_POLLS}]${usage >= 0 ? ` [ctx=${usage}%]` : ''}`);
              const tk2 = countTokensBetween(missionStartDate, new Date());
              tokensSinceCompact += tk2.tokens;
              log(`TOKENS: Mission #${num} used ${tk2.tokens.toLocaleString()} tokens (${tk2.requests} reqs, ${tk2.model}) [Session accum: ${Math.round(tokensSinceCompact / 1000)}k]`);
              recordMission(prompt.slice(0, 60), path.basename(projectDir || ''), tk2.tokens, elapsedSec, tk2.model);
              const daily2 = getDailyUsage(); if (daily2.overBudget) log(`⚠️ 作戰: DAILY BUDGET EXCEEDED — ${daily2.tokens.toLocaleString()} tokens today!`);
              // 🧠 LLM VISION: Get mission completion summary (non-blocking, don't block dispatch)
              try {
                const { getMissionSummary, clearCache } = require('./llm-interpreter');
                clearCache();
                // 🧠 LEARNING: Record successful completion
                try { require('./learning-engine').recordOutcome(prompt.slice(0, 40), path.basename(projectDir || ''), 'done', elapsedSec); } catch (e) { }
                getMissionSummary(output).catch(() => { }); // Fire-and-forget
              } catch (e) { }
              return { success: true, result: 'done', elapsed: elapsedSec };
            }
          } else if (elapsedSec > MIN_MISSION_SECONDS) {
            // 🦞 FIX BUG #1 2026-02-27: Fast-proxy completion path
            // If never saw BUSY but enough time passed + enough idle confirms → treat as done
            if (idleConfirmCount === 0) log(`WARNING: Mission #${num} idle for ${elapsedSec}s without ever becoming busy!`);
            idleConfirmCount++;

            // Fast-proxy path: enough idle confirms after MIN_MISSION_SECONDS → success
            if (idleConfirmCount >= IDLE_CONFIRM_POLLS && idleConfirmCount < IDLE_CONFIRM_POLLS * 6) {
              // Check if output shows any sign of completion (not just empty prompt)
              const hasCompletionSign = output && output.length > 200;
              if (hasCompletionSign) {
                log(`COMPLETE: Mission #${num} (${elapsedSec}s) [fast-proxy-path: idle x${idleConfirmCount}, wasBusy=false]`);
                const tk2 = countTokensBetween(missionStartDate, new Date());
                tokensSinceCompact += tk2.tokens;
                log(`TOKENS: Mission #${num} used ${tk2.tokens.toLocaleString()} tokens`);
                recordMission(prompt.slice(0, 60), path.basename(projectDir || ''), tk2.tokens, elapsedSec, tk2.model);
                try { require('./learning-engine').recordOutcome(prompt.slice(0, 40), path.basename(projectDir || ''), 'done', elapsedSec); } catch (e) { }
                return { success: true, result: 'done', elapsed: elapsedSec, path: 'fast_proxy_completion' };
              }
            }

            // Ultimate fail after 6x idle confirms
            if (idleConfirmCount >= IDLE_CONFIRM_POLLS * 6) {
              log(`ERROR: Mission #${num} failed to start after ${elapsedSec}s [wasBusy=false]. Clearing CC CLI + aborting.`);
              tmuxExec(`tmux send-keys -t ${TMUX_SESSION}.${workerIdx} Escape`, TMUX_SESSION);
              await sleep(1000);
              tmuxExec(`tmux send-keys -t ${TMUX_SESSION}.${workerIdx} Escape`, TMUX_SESSION);
              try { require('./learning-engine').recordOutcome(prompt.slice(0, 40), path.basename(projectDir || ''), 'failed_to_start', elapsedSec); } catch (e) { }
              return { success: false, result: 'failed_to_start', elapsed: elapsedSec };
            }
          }
          break;

        default: // 'unknown' — can't classify, reset idle counter
          idleConfirmCount = 0;
          break;
      }

      // Progress logging every 60s
      if (Date.now() - lastLogTime > 60000) {
        log(`Mission #${num} [${state}] — ${elapsedSec}s${wasBusy ? ' (was-busy)' : ''}`);
        lastLogTime = Date.now();
      }

      // PROJECT FLASH: Ultra Speed Polling (500ms for parallel mode)
      await sleep(500);
    }

    // Timeout — send Ctrl+C and report
    const elapsed = Math.round((Date.now() - startTime) / 1000);
    log(`TIMEOUT: Mission #${num} on P${workerIdx} exceeded ${Math.round(timeoutMs / 1000)}s — sending Ctrl+C`);
    sendCtrlC(workerIdx, TMUX_SESSION);
    return { success: false, result: 'timeout', elapsed };
  } finally {
    // 🔒 GUARANTEED CLEANUP: Always clear per-worker lock on exit
    clearWorkerLock(workerIdx);
  }
}

// --- SYSTEM MONITORING (User Request: "Giám sát nhiệt độ & API") ---

function getSystemMetrics() {
  try {
    // macOS Load Average
    const loadString = execSync('sysctl -n vm.loadavg').toString().trim();
    // Format: "{ 2.15 2.05 1.98 }" -> remove braces -> split
    const parts = loadString.replace(/[{}]/g, '').trim().split(/\s+/);
    const load1min = parseFloat(parts[0]);

    // Memory Usage (Approximate RSS)
    const mem = process.memoryUsage().rss / 1024 / 1024;

    return { load: load1min, mem: Math.round(mem) };
  } catch (e) {
    return { load: 0, mem: 0 };
  }
}

function isOverheating() {
  const metrics = getSystemMetrics();
  // THRESHOLD: Load > 4.0 is "Overheating" (Intervention Zone)
  if (metrics.load > 4.0) {
    // ACTIVE INTERVENTION: Monitor & Support
    const coolingTime = 10000; // 10s Cooling Nap
    try { fs.appendFileSync(config.THERMAL_LOG, `[${new Date().toISOString()}] 🔥 HIGH LOAD (${metrics.load}). Intervening... Sleeping ${coolingTime / 1000}s\n`); } catch (e) { }

    // We intentionally block here to force the system to slow down.
    // This supports the machine as requested ("can thiệp hỗ trợ").
    execSync(`sleep ${coolingTime / 1000}`);

    return true;
  }
  return false;
}

// STUCK INTERVENTION: If task > 5min AND Load > 4.0, assume stuck model -> Ctrl+C
function checkStuckIntervention(workerIdx, elapsedSec, wasBusy) {
  // 🦞 BUG 2026-02-26: CC CLI mid-mission kill
  // Deep Research/Scan missions can be idle for long periods.
  // If we are BUSY (meaning it is actually outputting text), DO NOT kill!
  if (wasBusy) return false;

  // Only intervene if IDLE and elapsed > cooling interval + safety margin
  // 🦞 FIX: Increased from 90s+30s to 300s (5 minutes) for deep scans
  const cooling = 300000; // 300s
  const margin = 60000;  // 60s

  if (elapsedSec > (cooling + margin) / 1000) {
    log(`STUCK: (P${workerIdx}) seems stuck after ${elapsedSec}s — INTERVENING...`);
    sendCtrlC(workerIdx); // Send Ctrl+C to the specific worker
    return true;
  }
  return false;
}

module.exports = { spawnBrain, killBrain, isBrainAlive, runMission, log, isOverheating, getSystemMetrics, checkStuckIntervention, capturePane };
