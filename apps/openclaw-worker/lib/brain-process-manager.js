const { execSync, spawn } = require('child_process');
const fs = require('fs');
const path = require('path');
const config = require('../config');

// Read API key: env var first, then ~/.mekong/api-key file fallback (for launchd)
function getApiKey() {
  if (process.env.ANTHROPIC_API_KEY) return process.env.ANTHROPIC_API_KEY;
  const keyFile = path.join(process.env.HOME || '', '.mekong', 'api-key');
  try { return fs.readFileSync(keyFile, 'utf-8').trim(); } catch(e) { return ''; }
}

let brainProcess = null;
let brainAlive = false;

function log(msg) {
  const timestamp = new Date().toISOString().slice(11, 19);
  const formatted = `[${timestamp}] 🦞 ${msg}\n`;
  process.stderr.write(formatted);
  try { fs.appendFileSync(config.LOG_FILE, formatted); } catch (e) {}
}

function spawnBrain() {
  if (brainAlive) return;
  log('🧠 SPAWNING PERSISTENT BRAIN');

  // Kill stale claude processes (intentional: ensures clean state for managed brain)
  try { execSync('pkill -x claude 2>/dev/null'); } catch(e) {}
  // Clean IPC files
  try { fs.unlinkSync(config.MISSION_FILE); } catch(e) {}
  try { fs.unlinkSync(config.DONE_FILE); } catch(e) {}

  brainProcess = spawn('expect', [config.EXPECT_SCRIPT, config.MEKONG_DIR, config.LOG_FILE], {
    cwd: config.MEKONG_DIR,
    env: {
      ...process.env,
      ANTHROPIC_BASE_URL: `http://127.0.0.1:${config.PROXY_PORT}`,
      ANTHROPIC_API_KEY: getApiKey(),
    },
    stdio: ['pipe', 'pipe', 'pipe'],
  });

  brainAlive = true;
  log(`✅ Brain spawned (PID: ${brainProcess.pid})`);

  brainProcess.stdout.on('data', () => {});
  brainProcess.stderr.on('data', () => {});
  brainProcess.on('close', (code) => {
    brainAlive = false;
    log(`⚠️ Brain exited (code: ${code}) — will respawn on next mission`);
    brainProcess = null;
  });
}

function killBrain() {
  if (brainProcess) {
    log('🔪 Killing brain process');
    brainProcess.kill('SIGTERM');
    setTimeout(() => {
      if (brainProcess && !brainProcess.killed) {
        brainProcess.kill('SIGKILL');
      }
    }, 5000);
  }
}

function isBrainAlive() { return brainAlive; }

module.exports = { spawnBrain, killBrain, isBrainAlive, log };
