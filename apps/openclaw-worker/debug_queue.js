const fs = require('fs');
const path = require('path');
const config = require('./config');

console.log('--- DEBUG START ---');
console.log('MEKONG_DIR:', config.MEKONG_DIR);
console.log('WATCH_DIR:', config.WATCH_DIR);
console.log('PROCESSED_DIR:', config.PROCESSED_DIR);
console.log('TASK_PATTERN:', config.TASK_PATTERN);

const filename = 'CRITICAL_brain_surgery.txt';
const filePath = path.join(config.WATCH_DIR, filename);
const processedPath = path.join(config.PROCESSED_DIR, filename);

console.log('Testing file:', filename);
console.log('filePath exists:', fs.existsSync(filePath));
console.log('processedPath exists:', fs.existsSync(processedPath));
console.log('Pattern match:', config.TASK_PATTERN.test(filename));

const queuedSet = new Set();
const processingSet = new Set();
const currentTaskFile = null;

const isDuplicate = queuedSet.has(filename) || processingSet.has(filename) || filename === currentTaskFile;
console.log('isDuplicate (simulated):', isDuplicate);

if (fs.existsSync(filePath) && !isDuplicate && !fs.existsSync(processedPath)) {
  console.log('SIMULATION: Enqueue WOULD succeed');
} else {
  console.log('SIMULATION: Enqueue WOULD FAIL');
}

// Check other files
const v2 = 'CRITICAL_mission_brain_surgery_v2.txt';
console.log('Testing v2:', v2);
console.log('v2 Pattern match:', config.TASK_PATTERN.test(v2));
console.log('v2 processedPath exists:', fs.existsSync(path.join(config.PROCESSED_DIR, v2)));

console.log('--- DEBUG END ---');
