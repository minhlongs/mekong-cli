const fs = require('fs');
const path = require('path');
const config = require('../config');
const { log, isBrainAlive } = require('./brain-process-manager');
const { isQueueEmpty } = require('./task-queue');

let emptyQueueCount = 0;
let lastGeneratedProject = null;
let intervalRef = null;

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
  intervalRef = setInterval(() => {
    try {
      const tasks = fs.readdirSync(config.WATCH_DIR).filter(f => config.TASK_PATTERN.test(f));
      if (tasks.length === 0 && isQueueEmpty()) {
        emptyQueueCount++;
        if (emptyQueueCount >= config.AUTO_CTO_EMPTY_THRESHOLD) {
          emptyQueueCount = 0;
          // Only generate if brain is alive
          if (!isBrainAlive()) {
            log('AUTO-CTO: Brain not alive — skipping task generation');
            return;
          }
          generateNextTask();
        }
      } else {
        emptyQueueCount = 0;
      }
    } catch (e) {}
  }, 5000);
}

function stopAutoCTO() {
  if (intervalRef) {
    clearInterval(intervalRef);
    intervalRef = null;
  }
}

function generateNextTask() {
  try {
    const state = loadState();
    state.autoScanCycle++;

    // Pick project, skipping the last-generated one to avoid consecutive repeats
    let projectIdx = (state.autoScanCycle - 1) % config.PROJECTS.length;
    let project = config.PROJECTS[projectIdx];
    if (project === lastGeneratedProject && config.PROJECTS.length > 1) {
      state.autoScanCycle++;
      projectIdx = (state.autoScanCycle - 1) % config.PROJECTS.length;
      project = config.PROJECTS[projectIdx];
    }

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
      lastGeneratedProject = project;
      log(`AUTO-CTO: Generated ${nextTask.id} for ${project}`);
      saveState(state);
    }
  } catch (error) {
    log(`AUTO-CTO error: ${error.message}`);
  }
}

module.exports = { startAutoCTO, stopAutoCTO };
