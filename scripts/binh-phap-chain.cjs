#!/usr/bin/env node
/**
 * binh-phap-chain.cjs — Binh Phap Chain Executor
 *
 * Auto-executes the 13 Binh Phap chapters in sequence with status tracking.
 * Each chapter maps to a Mekong CLI command for a specific C-level agent layer.
 *
 * Usage:
 *   node scripts/binh-phap-chain.cjs            # Run all pending chapters
 *   node scripts/binh-phap-chain.cjs --next     # Run only the next pending chapter
 *   node scripts/binh-phap-chain.cjs --status   # Show current progress
 *   node scripts/binh-phap-chain.cjs --reset    # Reset chain state to fresh start
 *
 * State file: .mekong/binh-phap-state.json
 */
'use strict';

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// ─── Paths ───────────────────────────────────────────────────────────────────

const SCRIPT_DIR = __dirname;
const PROJECT_ROOT = path.resolve(SCRIPT_DIR, '..');
const STATE_DIR = path.join(PROJECT_ROOT, '.mekong');
const STATE_FILE = path.join(STATE_DIR, 'binh-phap-state.json');

// ─── Chapter Definitions (from Binh Phap × Inverted Triangle) ────────────────

const CHAPTERS = [
  {
    number: 1,
    name: 'Strategy Assessment',
    vietnamese: 'Chien Luoc',
    layer: 'L2 CEO',
    agent: 'CEO/CFO',
    command: 'swot',
    description: 'Assessment and strategic planning via SWOT analysis',
  },
  {
    number: 2,
    name: 'Operations Runway',
    vietnamese: 'Van Hanh',
    layer: 'L3 COO',
    agent: 'COO/CHRO',
    command: 'audit resources',
    description: 'Runway and resource audit for operational readiness',
  },
  {
    number: 3,
    name: 'Win-Without-Fighting',
    vietnamese: 'Ky Thuat',
    layer: 'L5 CSO',
    agent: 'CSO',
    command: 'market scan',
    description: 'Market scanning for win-without-fighting opportunities',
  },
  {
    number: 4,
    name: 'Position Moat',
    vietnamese: 'Vi The',
    layer: 'L4 CTO',
    agent: 'CTO',
    command: 'audit tech',
    description: 'Technology moat audit for defensive positioning',
  },
  {
    number: 5,
    name: 'Momentum Growth',
    vietnamese: 'Da Tang Truong',
    layer: 'L5 CMO',
    agent: 'CMO',
    command: 'campaign',
    description: 'Growth campaign planning and momentum building',
  },
  {
    number: 6,
    name: 'Anti-Dilution',
    vietnamese: 'Linh Hoat',
    layer: 'L1 Founder',
    agent: 'Founder (Human)',
    command: 'cap-table',
    description: 'Cap table review and anti-dilution analysis',
  },
  {
    number: 7,
    name: 'Speed Sprint',
    vietnamese: 'Canh Tranh',
    layer: 'L5 CSO',
    agent: 'CSO',
    command: 'competitive',
    description: 'Competitive speed sprint for market advantage',
  },
  {
    number: 8,
    name: 'Pivot Workshop',
    vietnamese: 'Thich Ung',
    layer: 'L2 CEO',
    agent: 'CEO/CFO',
    command: 'brainstorm pivot',
    description: 'Pivot workshop to explore strategic adaptation options',
  },
  {
    number: 9,
    name: 'OKR Movement',
    vietnamese: 'Hanh Dong',
    layer: 'L3 COO',
    agent: 'COO/CHRO',
    command: 'okr',
    description: 'OKR implementation for operational alignment',
  },
  {
    number: 10,
    name: 'Market Entry',
    vietnamese: 'Dia Hinh',
    layer: 'L4 CTO',
    agent: 'CTO',
    command: 'deploy',
    description: 'Market entry deployment and terrain assessment',
  },
  {
    number: 11,
    name: 'Crisis Situations',
    vietnamese: 'Tinh Huong',
    layer: 'L1 Founder',
    agent: 'Founder (Human)',
    command: 'risk',
    description: 'Crisis scenario analysis and contingency planning',
  },
  {
    number: 12,
    name: 'Disruption Attack',
    vietnamese: 'Tan Cong',
    layer: 'L5 CSO',
    agent: 'CSO',
    command: 'launch',
    description: 'Disruptive launch strategy and market attack plan',
  },
  {
    number: 13,
    name: 'Competitive Intel',
    vietnamese: 'Tinh Bao',
    layer: 'L5 CMO',
    agent: 'CMO',
    command: 'intel',
    description: 'Competitive intelligence gathering and analysis',
  },
];

const TOTAL_CHAPTERS = CHAPTERS.length;

// ─── State Management ────────────────────────────────────────────────────────

function getDefaultState() {
  return {
    current_chapter: 1,
    completed_chapters: [],
    started_at: null,
    updated_at: null,
    status: 'paused',
    chapter_history: [],
  };
}

function loadState() {
  try {
    fs.mkdirSync(STATE_DIR, { recursive: true });
    const raw = fs.readFileSync(STATE_FILE, 'utf8');
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed.chapter_history)) {
      parsed.chapter_history = [];
    }
    if (!Array.isArray(parsed.completed_chapters)) {
      parsed.completed_chapters = [];
    }
    return parsed;
  } catch {
    return getDefaultState();
  }
}

function saveState(state) {
  fs.mkdirSync(STATE_DIR, { recursive: true });
  state.updated_at = new Date().toISOString();
  fs.writeFileSync(STATE_FILE, JSON.stringify(state, null, 2), 'utf8');
}

function resetState() {
  const fresh = getDefaultState();
  saveState(fresh);
  return fresh;
}

// ─── Chapter Execution ───────────────────────────────────────────────────────

function formatChapterHeader(chapter) {
  const bar = '='.repeat(60);
  const title = 'BINH PHAP - ' + chapter.vietnamese + ' (Chuong ' + chapter.number + ')';
  const subtitle = chapter.name + ' | ' + chapter.layer + ' | ' + chapter.agent;
  return '\n' + bar + '\n  ' + title + '\n  ' + subtitle + '\n  Command: /' + chapter.command + '\n' + bar + '\n';
}

function runMekongCommand(chapter) {
  const fullCommand = 'mekong ' + chapter.command;

  console.log('  Executing: ' + fullCommand);
  console.log('');

  try {
    const output = execSync(fullCommand, {
      cwd: PROJECT_ROOT,
      encoding: 'utf8',
      timeout: 300000,
      maxBuffer: 10 * 1024 * 1024,
      stdio: 'pipe',
    });

    const lines = output.split('\n').filter(function (l) { return l.trim().length > 0; });
    const resultSummary = lines.slice(-10).join('\n');

    return {
      success: true,
      exitCode: 0,
      outputSummary: resultSummary,
    };
  } catch (error) {
    var exitCode = 1;
    if (error.status !== undefined && error.status !== null) {
      exitCode = error.status;
    }
    var stderr = '';
    if (error.stderr) {
      stderr = error.stderr.trim();
    }
    var stdout = '';
    if (error.stdout) {
      stdout = error.stdout.trim();
    }
    var errorMessage = error.message || 'Unknown error';

    return {
      success: false,
      exitCode: exitCode,
      outputSummary: stdout.slice(0, 2000) || errorMessage.slice(0, 500),
      errorMessage: errorMessage,
      stderr: stderr.slice(0, 1000),
    };
  }
}

function executeChapter(state, chapter) {
  console.log(formatChapterHeader(chapter));
  console.log('  Description: ' + chapter.description);
  console.log('  Started at: ' + new Date().toISOString());
  console.log('');

  var result = runMekongCommand(chapter);

  var historyEntry = {
    chapter: chapter.number,
    name: chapter.name,
    vietnamese: chapter.vietnamese,
    layer: chapter.layer,
    command: chapter.command,
    status: result.success ? 'completed' : 'failed',
    started_at: state.updated_at || new Date().toISOString(),
    completed_at: new Date().toISOString(),
    exit_code: result.exitCode,
    output_summary: result.outputSummary,
  };

  if (result.success) {
    console.log('\n  OK Chapter ' + chapter.number + ' (' + chapter.name + ') completed successfully.');
  } else {
    console.log('\n  FAILED Chapter ' + chapter.number + ' (' + chapter.name + ') failed.');
    if (result.errorMessage) {
      console.log('  Error: ' + result.errorMessage);
    }
  }

  return historyEntry;
}

// ─── Display Functions ───────────────────────────────────────────────────────

function showStatus(state) {
  var bar = '='.repeat(60);
  console.log('\n' + bar);
  console.log('  BINH PHAP CHAIN STATUS');
  console.log(bar);
  console.log('  Status:          ' + state.status);
  console.log('  Current Chapter: ' + state.current_chapter + ' / ' + TOTAL_CHAPTERS);
  console.log('  Completed:       ' + state.completed_chapters.length + ' / ' + TOTAL_CHAPTERS);
  console.log('  Started At:      ' + (state.started_at || 'Not started'));
  console.log('  Last Updated:    ' + (state.updated_at || 'N/A'));
  console.log(bar);
  console.log('');

  if (state.chapter_history.length === 0) {
    console.log('  No chapters have been executed yet.\n');
    return;
  }

  console.log('  Chapter History:');
  console.log('  -----------------');

  for (var i = 0; i < state.chapter_history.length; i++) {
    var entry = state.chapter_history[i];
    var icon = entry.status === 'completed' ? 'OK' : 'XX';
    console.log('  ' + icon + ' Ch.' + String(entry.chapter) + ' ' + entry.name + ' [' + entry.layer + '] ' + entry.status);
  }

  var done = state.completed_chapters.length;
  var pct = Math.round((done / TOTAL_CHAPTERS) * 100);
  var progressBarLen = 30;
  var filled = Math.round((done / TOTAL_CHAPTERS) * progressBarLen);
  var empty = progressBarLen - filled;

  console.log('');
  console.log('  Progress: |' + '#'.repeat(filled) + '-'.repeat(empty) + '| ' + pct + '% (' + done + '/' + TOTAL_CHAPTERS + ')');
  console.log('');
}

function findNextChapter(state) {
  var completed = {};
  for (var i = 0; i < state.completed_chapters.length; i++) {
    completed[state.completed_chapters[i]] = true;
  }
  for (var j = 0; j < CHAPTERS.length; j++) {
    var ch = CHAPTERS[j];
    if (!completed[ch.number]) {
      return ch;
    }
  }
  return null;
}

function isChainComplete(state) {
  return state.completed_chapters.length >= TOTAL_CHAPTERS;
}

// ─── Main Execution ──────────────────────────────────────────────────────────

function main() {
  var args = process.argv.slice(2);
  var flagNext = args.indexOf('--next') !== -1;
  var flagStatus = args.indexOf('--status') !== -1;
  var flagReset = args.indexOf('--reset') !== -1;

  // Flag: --status
  if (flagStatus) {
    var state = loadState();
    showStatus(state);
    return;
  }

  // Flag: --reset
  if (flagReset) {
    console.log('\n  Resetting Binh Phap chain state...');
    resetState();
    console.log('  State file cleared. All chapters are pending.\n');
    return;
  }

  // Load state and execute
  var state = loadState();

  if (isChainComplete(state)) {
    console.log('\n  Binh Phap chain is already complete! All 13 chapters done.');
    console.log('  Use --status to see results, or --reset to start over.\n');
    return;
  }

  // Activate chain on first run
  if (!state.started_at) {
    state.started_at = new Date().toISOString();
  }
  state.status = 'active';

  // Determine which chapters to execute
  var chaptersToRun;
  if (flagNext) {
    var next = findNextChapter(state);
    if (!next) {
      console.log('\n  No pending chapters found. Chain may be complete.\n');
      return;
    }
    chaptersToRun = [next];
    console.log('  --next mode: executing chapter ' + next.number + ' (' + next.name + ')\n');
  } else {
    chaptersToRun = [];
    for (var k = 0; k < CHAPTERS.length; k++) {
      if (state.completed_chapters.indexOf(CHAPTERS[k].number) === -1) {
        chaptersToRun.push(CHAPTERS[k]);
      }
    }
    console.log('\n  BINH PHAP CHAIN -- executing ' + chaptersToRun.length + ' pending chapter(s)\n');
  }

  // Execute each pending chapter
  for (var m = 0; m < chaptersToRun.length; m++) {
    var chapter = chaptersToRun[m];
    var entry = executeChapter(state, chapter);

    // Update state
    state.chapter_history.push(entry);
    if (entry.status === 'completed') {
      state.completed_chapters.push(chapter.number);
      if (chapter.number >= state.current_chapter) {
        state.current_chapter = chapter.number + 1;
      }
    }

    // If chapter failed, pause the chain
    if (entry.status === 'failed') {
      state.status = 'paused';
      saveState(state);
      console.log('\n  Chain paused due to failure in chapter ' + chapter.number + '.');
      console.log('  Fix the issue and re-run to continue from this chapter.\n');
      process.exit(1);
    }

    saveState(state);
  }

  // Final status
  state.status = isChainComplete(state) ? 'completed' : 'active';
  state.current_chapter = state.completed_chapters.length + 1;
  if (state.current_chapter > TOTAL_CHAPTERS) {
    state.current_chapter = TOTAL_CHAPTERS;
  }
  saveState(state);

  console.log('\n  ' + '='.repeat(60));
  if (state.status === 'completed') {
    console.log('  BINH PHAP CHAIN COMPLETE -- All 13 chapters executed successfully.');
  } else {
    var remaining = TOTAL_CHAPTERS - state.completed_chapters.length;
    console.log('  BINH PHAP CHAIN PROGRESS -- ' + state.completed_chapters.length + ' done, ' + remaining + ' remaining.');
    console.log('  Run without flags to continue, or --next for one chapter at a time.');
  }
  console.log('  ' + '='.repeat(60) + '\n');
}

main();
