const brain = require('./openclaw-worker/lib/brain-tmux');
const config = require('./openclaw-worker/config');

console.log("🦞 INITIALIZING LOBSTER BRAIN LOGIC...");

// Kill legacy sessions
try {
    brain.killBrain();
    require('child_process').execSync('tmux kill-session -t lobster_team 2>/dev/null');
} catch (e) { }

// Spawn the authentic brain
brain.spawnBrain();

console.log(`
✅ LOBSTER LOGIC ACTIVATED!
   Session: tom_hum_brain
   Antigravity: ENABLED (via cook.js)
   Automation: ENABLED (Auto-Approve / State Machine)

👉 Attach now: tmux attach -t tom_hum_brain
`);
