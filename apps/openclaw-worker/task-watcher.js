#!/usr/bin/env node
/**
 * 🦞 TÔM HÙM (OpenClaw) Task Watcher - v10.0 INBOX MIGRATION
 * 
 * CORE CHANGE:
 * - Watch `~/mekong-cli/tasks/` instead of `/tmp`
 * - Pattern: `mission_*.txt`
 * - Logs: `~/tom_hum_cto.log`
 */

const fs = require('fs');
const { exec, execSync } = require('child_process');
const path = require('path');

const MEKONG_DIR = '/Users/macbookprom1/mekong-cli';
const WATCH_DIR = path.join(MEKONG_DIR, 'tasks');
const PROCESSED_DIR = path.join(WATCH_DIR, 'processed');
const LOG_FILE = '/Users/macbookprom1/tom_hum_cto.log';
const TASK_PATTERN = /^mission_.*\.txt$/;

if (!fs.existsSync(PROCESSED_DIR)) {
  fs.mkdirSync(PROCESSED_DIR, { recursive: true });
}

function log(msg) {
  const timestamp = new Date().toISOString().slice(11, 19);
  const formatted = `[${timestamp}] 🦞 ${msg}\n`;
  console.log(formatted.trim());
  try {
    fs.appendFileSync(LOG_FILE, formatted);
  } catch (e) {
    console.error('Log write failed:', e);
  }
}

log(`--- MISSION CONTROL v10.0 ONLINE ---`);
log(`Watching Inbox: ${WATCH_DIR}`);

/** 🦞 SUPREME COMMANDER ENGINE */
function executeTaskInTerminal(taskContent, taskFile) {
  return new Promise((resolve) => {
    const cleanContent = taskContent.replace(/\\!/g, '!').replace(/\\"/g, '"').trim();
    
    let projectDir = MEKONG_DIR;
    if (taskContent.includes('anima119')) projectDir = path.join(MEKONG_DIR, 'apps/anima119');
    else if (taskContent.includes('84tea')) projectDir = path.join(MEKONG_DIR, 'apps/84tea');
    else if (taskContent.includes('apex_os') || taskContent.includes('apex-os')) projectDir = path.join(MEKONG_DIR, 'apps/apex-os');
    else if (taskContent.includes('sophia')) projectDir = path.join(MEKONG_DIR, 'apps/sophia-ai-factory');
    else if (taskContent.includes('well')) projectDir = path.join(MEKONG_DIR, 'apps/well');

    const manifestoCmd = `cat ${MEKONG_DIR}/docs/CTO_MANIFESTO.md`;
    
    // 🌲 RANDOM FOREST DISPATCHER (Load Balancing)
    const isQwenRotation = Math.random() > 0.5;
    const proxyPort = isQwenRotation ? 8046 : 8045;
    const modelName = isQwenRotation ? 'qwen-coder-plus' : 'claude-sonnet-4-6';
    const apiKey = "sk-6219c93290f14b32b047342ca8b0bea9";
    
    log(`DISPATCHER: Selecting ${isQwenRotation ? '🐉 QWEN' : '🤖 SONNET'} (${proxyPort}) for this mission.`);
    
    // 🛠 UNIFIED SUPREME COMMAND (The "Execution Tank" Pattern)
    // We cd, set env, and THEN start claude with the mission as the first prompt
    const unifiedCmd = `cd ${projectDir} && export ANTHROPIC_BASE_URL=http://127.0.0.1:${proxyPort} && export ANTHROPIC_API_KEY=${apiKey} && ${manifestoCmd} && claude --model ${modelName} --dangerously-skip-permissions "/binh-phap implement: ${cleanContent}"`;
    
    log(`DEPLOYING UNIFIED COMMAND TO ${projectDir}`);

    try {
      execSync(`printf '%s' "${unifiedCmd.replace(/"/g, '\\"')}" | pbcopy`);
    } catch (e) { log(`Clipboard error: ${e.message}`); }

    const appleScript = `
tell application "System Events"
    -- 1. Focus the specific Antigravity app by bundle ID
    set antigravityProcs to (every process whose bundle identifier is "com.google.antigravity")
    if (count of antigravityProcs) > 0 then
        set theProc to item 1 of antigravityProcs
        set frontmost of theProc to true
        delay 1.5
        
        tell theProc
            -- 2. Force close any stuck Command Palette or Chat with triple ESC
            key code 53 -- ESC
            delay 0.3
            key code 53 -- ESC
            delay 0.3
            key code 53 -- ESC
            delay 0.8
            
            -- 3. Toggle Terminal Focus (Ctrl+\`)
            -- We do this twice with a small delay to ensure it's open and focused
            keystroke "\`" using {control down}
            delay 1.0
            
            -- 4. HARD RESET terminal prompt
            -- Multiple Ctrl+C is safer than Ctrl+D as it won't exit the shell itself
            keystroke "c" using {control down}
            delay 0.3
            keystroke "c" using {control down}
            delay 0.3
            keystroke "c" using {control down}
            delay 0.5
            
            -- Clear line and screen
            keystroke "u" using {control down} 
            delay 0.3
            keystroke "l" using {control down}
            delay 0.8
            
            -- 5. Paste Unified Command and Execute
            keystroke "v" using {command down}
            delay 1.2
            keystroke return
        end tell
    else
        log "Antigravity process not found"
    end if
end tell
`;

    log(`Triggering Supreme Command...`);
    exec(`osascript -e '${appleScript.replace(/'/g, "'\"'\"'")}'`, (error) => {
      if (error) log(`Script Error: ${error.message}`);
      else log(`MISSION DISPATCHED.`);
      setTimeout(() => resolve({ success: true }), 10000);
    });
  });
}

/** 🔄 QUEUE */
let isProcessing = false;
const queue = [];

async function processQueue() {
  if (isProcessing || queue.length === 0) return;
  isProcessing = true;
  const taskFile = queue.shift();
  const filePath = path.join(WATCH_DIR, taskFile);
  
  try {
    if (!fs.existsSync(filePath)) {
      log(`Ghost file ignored: ${taskFile}`);
      return;
    }
    const content = fs.readFileSync(filePath, 'utf-8').trim();
    log(`EXECUTING: ${taskFile}`);
    await executeTaskInTerminal(content, taskFile);
    
    fs.renameSync(filePath, path.join(PROCESSED_DIR, taskFile));
    log(`Archived: ${taskFile}`);
  } catch (error) {
    log(`Error: ${error.message}`);
  } finally {
    isProcessing = false;
    processQueue();
  }
}

function checkAndQueue(filename) {
  if (filename && TASK_PATTERN.test(filename)) {
    const filePath = path.join(WATCH_DIR, filename);
    if (fs.existsSync(filePath) && !queue.includes(filename)) {
      log(`DETECTED: ${filename}`);
      queue.push(filename);
      processQueue();
    }
  }
}

// Watchers
if (fs.existsSync(WATCH_DIR)) {
  fs.watch(WATCH_DIR, (eventType, filename) => checkAndQueue(filename));
}

setInterval(() => {
  const files = fs.readdirSync(WATCH_DIR);
  const tasks = files.filter(f => TASK_PATTERN.test(f));
  if (tasks.length > 0) log(`Poll found: ${tasks.join(', ')}`);
  tasks.forEach(checkAndQueue);
}, 5000);

process.on('SIGINT', () => { log('OFFLINE.'); process.exit(0); });
