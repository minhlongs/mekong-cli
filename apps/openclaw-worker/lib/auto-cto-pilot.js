const fs = require('fs');
const path = require('path');
const config = require('../config');
const { log } = require('./brain-process-manager');
const { isQueueEmpty } = require('./task-queue');

let emptyQueueCount = 0;

function loadState() {
  try {
    if (fs.existsSync(config.STATE_FILE)) {
      return JSON.parse(fs.readFileSync(config.STATE_FILE, 'utf-8'));
    }
  } catch(e) {}
  return { completedTasks: {}, autoScanCycle: 0 };
}

function saveState(state) {
  try { fs.writeFileSync(config.STATE_FILE, JSON.stringify(state, null, 2)); } catch(e) {}
}

function startAutoCTO() {
  setInterval(() => {
    const tasks = fs.readdirSync(config.WATCH_DIR).filter(f => config.TASK_PATTERN.test(f));
    if (tasks.length === 0 && isQueueEmpty()) {
      emptyQueueCount++;
      if (emptyQueueCount >= config.AUTO_CTO_EMPTY_THRESHOLD) {
        emptyQueueCount = 0;
        generateNextTask();
      }
    } else {
      emptyQueueCount = 0;
    }
  }, 5000);
}

function generateNextTask() {
  try {
    const state = loadState();
    state.autoScanCycle++;
    const project = config.PROJECTS[(state.autoScanCycle - 1) % config.PROJECTS.length];
    const projectDir = path.join(config.MEKONG_DIR, 'apps', project);

    if (!fs.existsSync(projectDir)) {
      saveState(state);
      return;
    }

    if (!state.completedTasks[project]) state.completedTasks[project] = [];
    const nextTask = config.BINH_PHAP_TASKS.find(t => !state.completedTasks[project].includes(t.id));

    if (nextTask) {
      const filename = `mission_${project.replace(/-/g, '_')}_auto_${nextTask.id}.txt`;
      fs.writeFileSync(path.join(config.WATCH_DIR, filename), `${nextTask.cmd} in ${project}`);
      state.completedTasks[project].push(nextTask.id);
      log(`🧠 AUTO-CTO: Generated ${nextTask.id} for ${project}`);
      saveState(state);
    }
  } catch (error) {
    log(`⚠️ AUTO-CTO error: ${error.message}`);
  }
}

module.exports = { startAutoCTO };
