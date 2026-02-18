/**
 * 🦞 LOBSTER TEAM ACTIVATOR
 * Spawns a 1 Brain + 3 Workers Tmux Session
 * Uses 'cook' wrapper for all workers to ensure Antigravity Protection.
 */

const { spawnSync, execSync } = require('child_process');
const path = require('path');

const SESSION = 'lobster_team';
const COOK_BIN = path.resolve(__dirname, 'antigravity-gateway/cook.js');

function run(cmd) {
    try {
        execSync(cmd, { stdio: 'inherit' });
    } catch (e) {
        console.error(`Failed: ${cmd}`, e.message);
    }
}

// 1. Kill Check
try {
    execSync(`tmux kill-session -t ${SESSION} 2>/dev/null`);
    console.log("🦞 Killed clear previous session.");
} catch (e) { }

// 2. Create Session (Pane 0: Brain/Supervisor)
// We use a simple monitor for Brain in this visual demo
console.log("🦞 Spawning Brain (Supervisor)...");
run(`tmux new-session -d -s ${SESSION} -n operations`);
run(`tmux send-keys -t ${SESSION}:0 'echo "🧠 BRAIN ONLINE (Supervisor)" && tail -f /dev/null' Enter`);
run(`tmux select-pane -t ${SESSION}:0 -T "BRAIN (Supervisor)"`);

// 3. Split Workers (Pane 1, 2, 3) -> 1 Brain + 3 Workers
// P1 -> 84tea
console.log("🦞 Spawning Worker 1 (84tea)...");
run(`tmux split-window -h -t ${SESSION}:0`);
run(`tmux send-keys -t ${SESSION}:0.1 "cd apps/84tea && ${COOK_BIN} claude" Enter`);
run(`tmux select-pane -t ${SESSION}:0.1 -T "WORKER 1 (84tea)"`);

// P2 -> apex-os
console.log("🦞 Spawning Worker 2 (apex-os)...");
run(`tmux split-window -v -t ${SESSION}:0.1`);
run(`tmux send-keys -t ${SESSION}:0.2 "cd apps/apex-os && ${COOK_BIN} claude" Enter`);
run(`tmux select-pane -t ${SESSION}:0.2 -T "WORKER 2 (apex-os)"`);

// P3 (Split from P0) -> sophia-ai-factory
console.log("🦞 Spawning Worker 3 (sophia)...");
run(`tmux split-window -v -t ${SESSION}:0.0`);
run(`tmux send-keys -t ${SESSION}:0.3 "cd apps/sophia-ai-factory && ${COOK_BIN} claude" Enter`);
run(`tmux select-pane -t ${SESSION}:0.3 -T "WORKER 3 (sophia)"`);

// 4. Layout
run(`tmux select-layout -t ${SESSION}:0 tiled`);

console.log(`
✅ LOBSTER TEAM ASSEMBLED!
   Session: ${SESSION}
   Topology: 1 Brain + 3 Workers
   Protection: Antigravity Gateway (Cook Wrapper)

👉 Attach now: tmux attach -t ${SESSION}
`);
