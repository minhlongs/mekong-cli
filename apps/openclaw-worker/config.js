const path = require('path');

const MEKONG_DIR = process.env.MEKONG_DIR || '/Users/macbookprom1/mekong-cli';

module.exports = {
  MEKONG_DIR,
  OPENCLAW_HOME: process.env.OPENCLAW_HOME || path.join(process.env.HOME || '', '.openclaw'),
  WATCH_DIR: path.join(MEKONG_DIR, 'tasks'),
  PROCESSED_DIR: path.join(MEKONG_DIR, 'tasks', 'processed'),
  LOG_FILE: process.env.TOM_HUM_LOG || '/Users/macbookprom1/tom_hum_cto.log',
  MISSION_FILE: '/tmp/tom_hum_next_mission.txt',
  DONE_FILE: '/tmp/tom_hum_mission_done',
  TASK_PATTERN: /^mission_.*\.txt$/,
  MISSION_TIMEOUT_MS: 45 * 60 * 1000,
  POLL_INTERVAL_MS: 3000,
  COOLING_INTERVAL_MS: 90000,
  AUTO_CTO_EMPTY_THRESHOLD: 60,
  STATE_FILE: path.join(MEKONG_DIR, 'tasks', '.tom_hum_state.json'),
  PROXY_PORT: parseInt(process.env.PROXY_PORT || '8080', 10),
  QWEN_PROXY_PORT: parseInt(process.env.QWEN_PROXY_PORT || '8081', 10),
  MODEL_NAME: 'claude-opus-4-6-thinking',
  QWEN_MODEL_NAME: process.env.QWEN_MODEL_NAME || 'qwen-coder-plus',
  // Engine selection: 'antigravity' (default, port 8080) or 'qwen' (port 8081)
  ENGINE: process.env.TOM_HUM_ENGINE || 'antigravity',
  // Dual-mode brain: 'direct' = claude -p per mission, 'tmux' = persistent tmux session
  BRAIN_MODE: process.env.TOM_HUM_BRAIN_MODE || 'direct',
  TMUX_SESSION: 'tom-hum-brain',
  TMUX_WIDTH: 200,
  TMUX_HEIGHT: 50,
  PROMPT_DEBOUNCE_MS: 2000,
  PROJECTS: ['84tea', 'apex-os', 'sophia-ai-factory', 'anima119', 'well'],
  BINH_PHAP_TASKS: [
    { id: 'console_cleanup', cmd: '/cook "Clean all console.log and debug statements from production code"' },
    { id: 'type_safety', cmd: '/cook "Fix all TypeScript any types and add proper type annotations"' },
    { id: 'a11y_audit', cmd: '/cook "WCAG 2.1 AA accessibility audit - fix alt text, ARIA labels, semantic HTML"' },
    { id: 'security_headers', cmd: '/cook "Implement security headers - CSP, HSTS, X-Frame-Options, XSS protection"' },
    { id: 'perf_audit', cmd: '/cook "Lighthouse performance audit - optimize bundle size, lazy loading"' },
    { id: 'i18n_sync', cmd: '/cook "Sync all i18n translation keys - fix missing translations"' },
  ],
};
