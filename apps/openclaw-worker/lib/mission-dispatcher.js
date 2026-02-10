const fs = require('fs');
const path = require('path');
const config = require('../config');
const { log, isBrainAlive, spawnBrain } = require('./brain-process-manager');

// Project routing: detect project from task content
function detectProjectDir(taskContent) {
  const lower = taskContent.toLowerCase();
  const routes = {
    '84tea': 'apps/84tea', tea: 'apps/84tea',
    apex: 'apps/apex-os',
    anima: 'apps/anima119',
    sophia: 'apps/sophia-ai-factory',
    well: 'apps/well',
  };
  for (const [keyword, dir] of Object.entries(routes)) {
    if (lower.includes(keyword)) return path.join(config.MEKONG_DIR, dir);
  }
  return config.MEKONG_DIR;
}

function buildPrompt(taskContent) {
  const clean = taskContent.replace(/\\!/g, '!').replace(/\\"/g, '"').trim();
  const safe = clean.replace(/[()$`\\!]/g, ' ').replace(/\s+/g, ' ').trim();
  return `/binh-phap implement: ${safe} /cook`;
}

// Atomic write: tmp file + rename (prevents partial reads)
function dispatchMission(prompt) {
  try { fs.unlinkSync(config.DONE_FILE); } catch(e) {}
  const tmpFile = config.MISSION_FILE + '.tmp';
  fs.writeFileSync(tmpFile, prompt);
  fs.renameSync(tmpFile, config.MISSION_FILE);
  log('📨 Mission delivered (atomic write)');
}

// Poll done file, return result string
function waitForCompletion(timeoutMs) {
  return new Promise((resolve) => {
    const startTime = Date.now();

    const pollDone = setInterval(() => {
      const elapsed = Math.round((Date.now() - startTime) / 1000);

      if (fs.existsSync(config.DONE_FILE)) {
        clearInterval(pollDone);
        clearInterval(statusLog);
        const result = fs.readFileSync(config.DONE_FILE, 'utf-8').trim();
        try { fs.unlinkSync(config.DONE_FILE); } catch(e) {}
        log(`🏁 MISSION COMPLETE! (${elapsed}s) — ${result}`);
        resolve({ success: result === 'done', result, elapsed });
        return;
      }

      if (!isBrainAlive()) {
        clearInterval(pollDone);
        clearInterval(statusLog);
        log(`❌ Brain died during mission (${elapsed}s)`);
        resolve({ success: false, result: 'brain_died', elapsed });
        return;
      }

      if (elapsed * 1000 > timeoutMs) {
        clearInterval(pollDone);
        clearInterval(statusLog);
        log(`⏰ Mission timeout (${elapsed}s)`);
        resolve({ success: false, result: 'timeout', elapsed });
      }
    }, config.POLL_INTERVAL_MS);

    // CPU status every 60s
    const statusLog = setInterval(() => {
      const elapsed = Math.round((Date.now() - startTime) / 1000);
      try {
        const { execSync } = require('child_process');
        const cpu = execSync(
          `ps aux | grep -E "claude" | grep -v grep | grep -v proxy | grep -v chroma | awk '{sum+=$3} END {print sum}'`,
          { encoding: 'utf-8' }
        ).trim();
        log(`⏳ CC CLI working — ${elapsed}s — ${cpu}% CPU`);
      } catch(e) {}
    }, 60000);
  });
}

// Full dispatch flow: build prompt → ensure brain → dispatch → wait
async function executeTask(taskContent, taskFile) {
  const projectDir = detectProjectDir(taskContent);
  const prompt = buildPrompt(taskContent);
  log(`PROJECT: ${projectDir}`);
  log(`PROMPT: ${prompt.slice(0, 120)}...`);

  if (!isBrainAlive()) {
    log('🔄 Brain dead — respawning...');
    spawnBrain();
    await new Promise(r => setTimeout(r, 15000)); // Wait for brain init
  }

  dispatchMission(prompt);
  return waitForCompletion(config.MISSION_TIMEOUT_MS);
}

module.exports = { executeTask, buildPrompt, dispatchMission, waitForCompletion, detectProjectDir };
