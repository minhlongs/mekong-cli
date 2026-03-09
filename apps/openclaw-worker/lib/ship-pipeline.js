/**
 * Ship Pipeline — Quản lý 5 phase ZERO-TO-SHIP cho mỗi project
 *
 * Phase 1: SCOUT   → /scout "scan project health, find critical bugs"
 * Phase 2: FIX     → /cook "fix all critical issues found by scout"
 * Phase 3: TEST    → /test "run full test suite"
 * Phase 4: REVIEW  → /review:codebase "audit code quality + security"
 * Phase 5: SHIP    → /check-and-commit "commit + push if all GREEN"
 */

const fs = require('fs');
const path = require('path');
const config = require('../config');

// File lưu trạng thái pipeline — cùng file với state Tôm Hùm
const PIPELINE_STATE_FILE = config.STATE_FILE;

// Định nghĩa 5 phase của ship pipeline
const PHASES = [
  {
    id: 1,
    name: 'SCOUT',
    // Quét sức khỏe project, tìm bugs nghiêm trọng
    command: '/scout "scan project health, find all critical bugs and issues"',
  },
  {
    id: 2,
    name: 'FIX',
    // Sửa tất cả vấn đề nghiêm trọng tìm được ở phase SCOUT
    command: '/cook "fix all critical issues found by scout — no git commit yet" --auto',
  },
  {
    id: 3,
    name: 'TEST',
    // Chạy toàn bộ test suite
    command: '/test "run full test suite, report failures"',
  },
  {
    id: 4,
    name: 'REVIEW',
    // Kiểm tra chất lượng code và bảo mật
    command: '/review:codebase "audit code quality, security, type safety"',
  },
  {
    id: 5,
    name: 'SHIP',
    // Commit + push nếu tất cả GREEN
    command: '/check-and-commit "all phases passed — commit and push to production"',
  },
];

// --- Đọc/ghi trạng thái pipeline ---

function loadPipelineState() {
  try {
    if (fs.existsSync(PIPELINE_STATE_FILE)) {
      const raw = JSON.parse(fs.readFileSync(PIPELINE_STATE_FILE, 'utf-8'));
      return raw.pipelines || {};
    }
  } catch (e) { /* bỏ qua lỗi đọc file */ }
  return {};
}

function savePipelineState(pipelines) {
  try {
    // Đọc state hiện tại để merge — không ghi đè các field khác
    let existing = {};
    if (fs.existsSync(PIPELINE_STATE_FILE)) {
      try { existing = JSON.parse(fs.readFileSync(PIPELINE_STATE_FILE, 'utf-8')); } catch (e) { }
    }
    const merged = Object.assign({}, existing, { pipelines });
    const tmp = `${PIPELINE_STATE_FILE}.tmp`;
    fs.writeFileSync(tmp, JSON.stringify(merged, null, 2));
    fs.renameSync(tmp, PIPELINE_STATE_FILE);
  } catch (e) { /* atomic write thất bại — bỏ qua */ }
}

function getProjectState(projectName) {
  const all = loadPipelineState();
  return all[projectName] || null;
}

// --- API công khai ---

/**
 * Lấy command cho phase tiếp theo của project.
 * Trả về null nếu pipeline đã hoàn thành hoặc chưa khởi tạo.
 */
function getNextPhaseCommand(projectName) {
  const all = loadPipelineState();
  const state = all[projectName];

  // Chưa có pipeline → bắt đầu phase 1
  if (!state) {
    return PHASES[0].command;
  }

  // Đã ship xong
  if (state.currentPhase > PHASES.length) {
    return null;
  }

  // Phase chưa hoàn thành → trả về command của phase hiện tại
  const phase = PHASES.find(p => p.id === state.currentPhase);
  return phase ? phase.command : null;
}

/**
 * Đánh dấu phase hiện tại hoàn thành, chuyển sang phase tiếp theo.
 * result: 'PASS' | 'FAIL' | 'SKIP'
 */
function advancePhase(projectName, result) {
  const all = loadPipelineState();
  const state = all[projectName] || {
    currentPhase: 1,
    phaseResults: {},
    startedAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  };

  const donedPhase = state.currentPhase;
  state.phaseResults[donedPhase] = result;
  state.updatedAt = new Date().toISOString();

  if (result === 'PASS' || result === 'SKIP') {
    state.currentPhase = donedPhase + 1;
  }
  // FAIL → giữ nguyên phase, thử lại lần sau

  all[projectName] = state;
  savePipelineState(all);
  return state;
}

/**
 * Trả về trạng thái pipeline hiện tại của project.
 */
function getPipelineStatus(projectName) {
  return getProjectState(projectName);
}

/**
 * Reset pipeline về phase 1.
 */
function resetPipeline(projectName) {
  const all = loadPipelineState();
  all[projectName] = {
    currentPhase: 1,
    phaseResults: {},
    startedAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  };
  savePipelineState(all);
}

/**
 * Kiểm tra xem pipeline đã hoàn thành tất cả 5 phase PASS chưa.
 */
function isShipComplete(projectName) {
  const state = getProjectState(projectName);
  if (!state) return false;
  if (state.currentPhase <= PHASES.length) return false;
  // Kiểm tra tất cả phase phải PASS
  for (const phase of PHASES) {
    if (state.phaseResults[phase.id] !== 'PASS') return false;
  }
  return true;
}

/**
 * Lấy tên phase theo ID.
 */
function getPhaseName(phaseId) {
  const phase = PHASES.find(p => p.id === phaseId);
  return phase ? phase.name : 'UNKNOWN';
}

module.exports = {
  PHASES,
  getNextPhaseCommand,
  advancePhase,
  getPipelineStatus,
  resetPipeline,
  isShipComplete,
  getPhaseName,
};
