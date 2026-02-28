const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

console.log("🔥 FORCE IGNITE: ANTIGRAVITY REALTIME ENGINE (3.0 Pro High)...");

// 1. Kill Everything
try {
    execSync('tmux kill-session -t mission_control 2>/dev/null');
    execSync('tmux kill-session -t tom_hum_brain 2>/dev/null');
    execSync('tmux kill-session -t lobster_team 2>/dev/null');
    console.log("💥 Killed old sessions.");
} catch (e) { }

// 2. Start Mission Control (Dispatcher)
try {
    execSync('tmux new-session -d -s mission_control "node apps/openclaw-worker/task-watcher.js"');
    console.log("✅ Mission Control STARTED.");
} catch (e) { console.error("Mission Control Failed", e.message); }

// 3. Start Lobster Brain (Workers)
try {
    // Use the Logic runner which calls brain-tmux.js
    execSync('node apps/run-lobster-logic.js', { stdio: 'inherit' });
    console.log("✅ Lobster Brain STARTED.");
} catch (e) { console.error("Lobster Brain Failed", e.message); }

// 4. INJECT IMMEDIATE TASK (Force Realtime Action)
const taskFile = path.join(__dirname, 'tasks', 'mission_REALTIME_IGNITION.txt');
const prompt = `
/plan:hard "REALTIME IGNITION: Analyze the current codebase state of all projects (84tea, apex-os, sophia). Identify the top 3 critical bottlenecks. Output a summary report immediately."
`;
// Ensure tasks dir exists
if (!fs.existsSync(path.join(__dirname, 'tasks'))) fs.mkdirSync(path.join(__dirname, 'tasks'));

fs.writeFileSync(taskFile, prompt.trim());
console.log(`🚀 INJECTED TASK: ${taskFile}`);

console.log(`
⚡️ SYSTEM IS RUNNING REALTIME.
   Mode: Gemini 1.5 Pro (High Tier)
   Action: Workers are picking up 'mission_REALTIME_IGNITION.txt' NOW.

👉 Monitor: tmux attach -t tom_hum_brain
`);
