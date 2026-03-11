const { execSync } = require('child_process');

function stripAnsi(text) {
    return text
        .replace(/\x1B\[[0-9;?]*[A-Za-z]/g, '')
        .replace(/\x1B\][^\x07\x1B]*(?:\x07|\x1B\\)/g, '')
        .replace(/\x1B[()][A-Za-z0-9]/g, '')
        .replace(/\x1B[A-Za-z]/g, '')
        .replace(/[\x00-\x08\x0E-\x1F\x7F]/g, '');
}

const out = execSync(`tmux capture-pane -t tom_hum_brain:0.0 -p -S -50`, { encoding: 'utf-8' });
const cleanOut = stripAnsi(out);
const lines = cleanOut.split('\n');
console.log("LAST 10 RAW CLEAN LINES:");
console.log(lines.slice(-10));

console.log("\nPOP LOOP LOGIC:");
let count = 0;
while (lines.length > 0 && !lines[lines.length - 1].trim()) {
    const popped = lines.pop();
    console.log(`Popped line: "${popped}"`);
    count++;
}
console.log(`Total popped: ${count}`);

console.log("\nREMAINING LAST 5 LINES:");
console.log(lines.slice(-5));
