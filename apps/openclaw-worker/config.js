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
  AUTO_CTO_EMPTY_THRESHOLD: 6, // 6 polls × 5s = 30s idle → generate next task
  STATE_FILE: path.join(MEKONG_DIR, 'tasks', '.tom_hum_state.json'),
  PROXY_PORT: parseInt(process.env.PROXY_PORT || '8080', 10),
  QWEN_PROXY_PORT: parseInt(process.env.QWEN_PROXY_PORT || '8081', 10),
  MODEL_NAME: 'claude-opus-4-6-thinking',
  QWEN_MODEL_NAME: process.env.QWEN_MODEL_NAME || 'qwen-coder-plus',
  // Engine selection: 'antigravity' (default, port 8080) or 'qwen' (port 8081)
  ENGINE: process.env.TOM_HUM_ENGINE || 'antigravity',
  // Brain modes: 'external' (default) = visible terminal, 'interactive' = expect PTY, 'direct' = claude -p, 'tmux' = persistent tmux
  BRAIN_MODE: process.env.TOM_HUM_BRAIN_MODE || 'external',
  EXPECT_SCRIPT: path.join(MEKONG_DIR, 'scripts', 'tom-hum-dispatch.exp'),
  TMUX_SESSION: 'tom-hum-brain',
  TMUX_WIDTH: 200,
  TMUX_HEIGHT: 50,
  PROMPT_DEBOUNCE_MS: 2000,
  PROJECTS: ['sophia-ai-factory', 'wellnexus', 'apex-os', '84tea', 'anima119'],
  // Rule: Match ClaudeKit /commands to situation — NOT blind /cook
  BINH_PHAP_TASKS: [
    { id: 'console_cleanup', cmd: '/cook "Clean all console.log and debug statements from production code"' },
    { id: 'type_safety', cmd: '/review "Audit TypeScript any types — report all locations needing proper type annotations"' },
    { id: 'a11y_audit', cmd: '/review "WCAG 2.1 AA accessibility audit — report alt text, ARIA labels, semantic HTML issues"' },
    { id: 'security_scan', cmd: '/review "Security audit — check CSP headers, XSS vectors, exposed secrets, CORS config"' },
    { id: 'perf_audit', cmd: '/review "Performance audit — bundle size, lazy loading, image optimization, Core Web Vitals"' },
    { id: 'test_suite', cmd: '/test "Run full test suite, report failures and coverage gaps"' },
    { id: 'debug_errors', cmd: '/debug "Investigate any runtime errors, unhandled rejections, or console warnings in production"' },
    { id: 'i18n_sync', cmd: '/cook "Sync all i18n translation keys — fix missing translations across all locales"' },
    { id: 'tech_debt', cmd: '/review:codebase "Full codebase review — TODO/FIXME/HACK count, dead code, circular deps"' },
  ],
};
