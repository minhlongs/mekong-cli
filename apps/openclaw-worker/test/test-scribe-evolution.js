const scribe = require('../scribe-daemon');
const fs = require('fs');
const path = require('path');
const config = require('../config');

console.log('🧪 Testing Scribe Daemon Evolution Capabilities...');

// Mock Data
const mockWin = {
    instruction: "Test Mission: Implement Scribe Recording",
    input: "Before implementation",
    output: "After implementation",
    thinking: "I should test if the file is created.",
    project: "openclaw-worker"
};

// 1. Record Win
console.log('1. Calling recordWin()...');
scribe.recordWin(mockWin);

// 2. Verify File
const winsFile = path.join(config.MEKONG_DIR, 'dataset', 'wins.jsonl');
if (fs.existsSync(winsFile)) {
    console.log('✅ wins.jsonl exists.');
    const content = fs.readFileSync(winsFile, 'utf8');
    if (content.includes('Test Mission')) {
        console.log('✅ Win Data successfully recorded!');
        console.log('------------------------------------------------');
        console.log(content.trim().split('\n').pop()); // Show last line
        console.log('------------------------------------------------');
    } else {
        console.error('❌ Win Data NOT found in file.');
        process.exit(1);
    }
} else {
    console.error('❌ wins.jsonl was NOT created.');
    process.exit(1);
}

console.log('🎉 Scribe Data Flywheel Test PASSED');
process.exit(0);
