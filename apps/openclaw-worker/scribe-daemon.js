const fs = require('fs');
const path = require('path');
const config = require('./config');
const QL = require('./lib/quan-luat-enforcer');

// ═══════════════════════════════════════════════════════════════
// 🏯 SCRIBE DAEMON — 書記 (Thư Ký)
// ═══════════════════════════════════════════════════════════════
// Rank: THU_KY (Thư Ký — Secretary)
// Territory: memory
// 36 Kế: #27 Giả Si Bất Điên
// Điều 3: CHỈ LOG + SUMMARIZE, KHÔNG DELETE
// Điều 8: Liên lạc không đứt — log phải luôn chạy
// ═══════════════════════════════════════════════════════════════

const DAEMON_NAME = 'scribe';
const DAEMON_RANK = QL.RANKS[DAEMON_NAME];
const SCRIBE_INTERVAL = 10 * 60 * 1000;
const LOG_FILE = config.LOG_FILE;
const MEMORY_DIR = path.join(config.MEKONG_DIR, 'memory');

if (!fs.existsSync(MEMORY_DIR)) fs.mkdirSync(MEMORY_DIR);

async function callGeminiFlash(prompt) {
  const MODEL = 'gemini-2.5-flash';
  if (!QL.validateModelTier(DAEMON_NAME, MODEL)) return null;

  try {
    const PROXY_URL = 'http://127.0.0.1:8080/v1/messages';
    const response = await fetch(PROXY_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: MODEL,
        messages: [
          { role: "user", content: `You are the Scribe of AgencyOS. Summarize the provided system logs into a concise bulleted list of: Completed Missions, Critical Errors, and System State changes. Return Markdown. \n\n${prompt}` }
        ],
        max_tokens: 4096,
        temperature: 0.2
      })
    });

    if (!response.ok) {
        const errText = await response.text();
        throw new Error(`API Error: ${response.status} - ${errText}`);
    }

    const data = await response.json();
    return data.content[0].text.trim();
  } catch (e) {
    QL.logQuanLuat(DAEMON_NAME, `❌ API Call Failed: ${e.message}`);
    return null;
  }
}

async function scribeLoop() {
  QL.logQuanLuat(DAEMON_NAME, '📜 Scribe Daemon STARTED');

  setInterval(async () => {
    try {
      if (!QL.checkTerritory(DAEMON_NAME, 'log_summary')) return;
      if (!fs.existsSync(LOG_FILE)) return;

      const stats = fs.statSync(LOG_FILE);
      const start = Math.max(0, stats.size - 50000);
      const stream = fs.createReadStream(LOG_FILE, { start, encoding: 'utf8' });

      let logContent = '';
      for await (const chunk of stream) { logContent += chunk; }
      if (!logContent.trim()) return;

      QL.logQuanLuat(DAEMON_NAME, 'Reading logs & Consulting Gemini Flash...');
      const summary = await callGeminiFlash(logContent);

      if (summary) {
        const date = new Date().toISOString().split('T')[0];
        const memoryFile = path.join(MEMORY_DIR, `log_summary_${date}.md`);
        const entry = `\n## Entry: ${new Date().toLocaleTimeString()}\n\n${summary}\n\n---\n`;
        fs.appendFileSync(memoryFile, entry);
        QL.logQuanLuat(DAEMON_NAME, `✍️ Wrote summary to ${memoryFile}`);
        QL.createSignal(DAEMON_NAME, 'sage', 'MEMORY_UPDATED', { file: memoryFile }, 'LOW');
      }
    } catch (err) {
      QL.logQuanLuat(DAEMON_NAME, `❌ Error: ${err.message}`);
    }
  }, SCRIBE_INTERVAL);
}

scribeLoop();
