const fs = require('fs');
const path = require('path');
const config = require('./config'); // Use centralized config
const QL = require('./lib/quan-luat-enforcer');

// ═══════════════════════════════════════════════════════════════
// 🏯 SCRIBE DAEMON — 書記 (Thư Ký) & 🧬 EVOLUTIONARY HISTORIAN
// ═══════════════════════════════════════════════════════════════
// Rank: THU_KY (Secretary) -> SU_QUAN (Historian)
// Territory: memory, dataset
// Mission: 
// 1. Summarize Logs (Daily Ops)
// 2. Capture 'Wins' (Self-Training Data Flywheel)
// ═══════════════════════════════════════════════════════════════

const DAEMON_NAME = 'scribe';
const SCRIBE_INTERVAL = 10 * 60 * 1000; // 10 minutes
const LOG_FILE = config.LOG_FILE;
const MEMORY_DIR = path.join(config.MEKONG_DIR, 'memory');
const DATASET_DIR = path.join(config.MEKONG_DIR, 'dataset');
const WINS_FILE = path.join(DATASET_DIR, 'wins.jsonl');

// Ensure directories
if (!fs.existsSync(MEMORY_DIR)) fs.mkdirSync(MEMORY_DIR, { recursive: true });
if (!fs.existsSync(DATASET_DIR)) fs.mkdirSync(DATASET_DIR, { recursive: true });

// --- AGI Evolution: Data Collection ---

/**
 * Record a successful mission for self-training
 * @param {object} winData { instruction, input, output, thinking, project }
 */
function recordWin(winData) {
  try {
    const entry = {
      instruction: winData.instruction,
      input: winData.input || '',
      output: winData.output || '',
      thinking: winData.thinking || '',
      status: 'success',
      project: winData.project || 'unknown',
      timestamp: Date.now(),
      model_used: config.MODEL_NAME || 'unknown' // Track which model achieved this
    };

    fs.appendFileSync(WINS_FILE, JSON.stringify(entry) + '\n');
    QL.logQuanLuat(DAEMON_NAME, `🧬 Captured Win for Self-Training: ${winData.instruction.substring(0, 50)}...`);
  } catch (e) {
    QL.logQuanLuat(DAEMON_NAME, `❌ Failed to record win: ${e.message}`);
  }
}

// --- Legacy Scribe: Log Summarization ---

async function callCloudBrain(prompt) {
  // Use Configured Model or Fallback
  const MODEL = config.FALLBACK_MODEL_NAME || 'gemini-2.0-flash';

  try {
    // FIXED: Use CLOUD_BRAIN_URL (Serveo/Ollama/Colab)
    const BRAIN_URL = `${config.CLOUD_BRAIN_URL}/v1/chat/completions`;

    // Fallback if BRAIN_URL is not set or invalid (though config should catch this)
    if (!BRAIN_URL || BRAIN_URL.includes('undefined')) {
      throw new Error('CLOUD_BRAIN_URL is undefined.');
    }

    const response = await fetch(BRAIN_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: MODEL,
        messages: [
          { role: "system", content: "You are the Scribe of AgencyOS. Summarize logs into concise markdown: Completed Missions, Critical Errors, System State." },
          { role: "user", content: prompt }
        ],
        temperature: 0.2
      })
    });

    if (!response.ok) throw new Error(`API Error: ${response.status}`);
    const data = await response.json();
    return data.choices[0].message.content.trim();
  } catch (e) {
    QL.logQuanLuat(DAEMON_NAME, `❌ Brain Call Failed: ${e.message}`);
    return null;
  }
}

async function scribeLoop() {
  QL.logQuanLuat(DAEMON_NAME, '📜 Scribe Daemon STARTED (Evolution Ready)');

  setInterval(async () => {
    try {
      // 1. Log Summarization Task
      if (fs.existsSync(LOG_FILE)) {
        const stats = fs.statSync(LOG_FILE);
        if (stats.size > 0 && stats.size < 500000) { // Safety limit
          // Placeholder for actual summarization logic
          // We avoid doing it in this refactor to keep changes focused on structure
        }
      }
    } catch (err) {
      QL.logQuanLuat(DAEMON_NAME, `❌ Error: ${err.message}`);
    }
  }, SCRIBE_INTERVAL);
}

// Export for use by other daemons (so Reviewer can call `recordWin`)
module.exports = { scribeLoop, recordWin };

if (require.main === module) {
  const args = process.argv.slice(2);
  if (args.includes('--record-win')) {
    // Automated Win Recording Triggered by CI/Test
    // Ideally, we would parse a report file here.
    // For now, we record a "Test Suite Passed" win.
    recordWin({
      instruction: "Automated Test Suite Verification",
      input: "npm test",
      output: "PASS",
      thinking: "Tests passed, code is verified. capturing snapshot.",
      project: config.PROJECT_NAME || "openclaw-worker"
    });
  } else {
    scribeLoop();
  }
}
