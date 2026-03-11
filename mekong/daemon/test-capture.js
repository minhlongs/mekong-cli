const { execSync } = require('child_process');

function stripAnsi(text) {
    return text
        .replace(/\x1B\[[0-9;?]*[A-Za-z]/g, '')
        .replace(/\x1B\][^\x07\x1B]*(?:\x07|\x1B\\)/g, '')
        .replace(/\x1B[()][A-Za-z0-9]/g, '')
        .replace(/\x1B[A-Za-z]/g, '')
        .replace(/[\x00-\x08\x0E-\x1F\x7F]/g, '');
}

function getCleanTail(output, n) {
    const lines = stripAnsi(output).split('\n');
    while (lines.length > 0 && !lines[lines.length - 1].trim()) {
        lines.pop();
    }
    return lines.slice(-n);
}

const out = execSync(`tmux capture-pane -t tom_hum_brain:0.0 -p -S -50`, { encoding: 'utf-8' });
console.log("RAW TAIL:");
console.log(out.split('\n').slice(-15).join('\n'));

console.log("\nCLEAN TAIL:");
console.log(getCleanTail(out, 15).join('\n'));

console.log("\nIS BUSY?");
let busy = false;
for (const line of getCleanTail(out, 10)) {
    const t = line.trim();
    if (t.includes('❯') || /^>\s*$/.test(t)) {
        console.log("FOUND PROMPT: " + t);
        busy = false;
        break;
    }
}
console.log(busy);
