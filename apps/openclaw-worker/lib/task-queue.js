const fs = require('fs');
const path = require('path');
const config = require('../config');
const { log } = require('./brain-process-manager');
const { executeTask } = require('./mission-dispatcher');

let isProcessing = false;
const queue = [];

async function processQueue() {
  if (isProcessing || queue.length === 0) return;
  isProcessing = true;
  const taskFile = queue.shift();
  const filePath = path.join(config.WATCH_DIR, taskFile);

  try {
    if (!fs.existsSync(filePath)) {
      log(`Ghost file ignored: ${taskFile}`);
      return;
    }
    const content = fs.readFileSync(filePath, 'utf-8').trim();
    log(`EXECUTING: ${taskFile}`);
    await executeTask(content, taskFile);
    fs.renameSync(filePath, path.join(config.PROCESSED_DIR, taskFile));
    log(`Archived: ${taskFile}`);
  } catch (error) {
    log(`Error: ${error.message}`);
  } finally {
    isProcessing = false;
    processQueue();
  }
}

function enqueue(filename) {
  if (filename && config.TASK_PATTERN.test(filename)) {
    const filePath = path.join(config.WATCH_DIR, filename);
    if (fs.existsSync(filePath) && !queue.includes(filename)) {
      log(`DETECTED: ${filename}`);
      queue.push(filename);
      processQueue();
    }
  }
}

function startWatching() {
  // Ensure processed dir exists
  if (!fs.existsSync(config.PROCESSED_DIR)) {
    fs.mkdirSync(config.PROCESSED_DIR, { recursive: true });
  }

  // fs.watch for instant detection
  if (fs.existsSync(config.WATCH_DIR)) {
    fs.watch(config.WATCH_DIR, (eventType, filename) => enqueue(filename));
  }

  // Periodic poll as backup (every 5s)
  setInterval(() => {
    const files = fs.readdirSync(config.WATCH_DIR);
    const tasks = files.filter(f => config.TASK_PATTERN.test(f));
    if (tasks.length > 0) log(`Poll found: ${tasks.join(', ')}`);
    tasks.forEach(enqueue);
  }, 5000);
}

function isQueueEmpty() { return queue.length === 0 && !isProcessing; }

module.exports = { startWatching, isQueueEmpty, enqueue };
