const { interpretState } = require('./lib/llm-interpreter');
const { execSync } = require('child_process');

async function test() {
    for (let pIdx = 0; pIdx < 2; pIdx++) {
        try {
            console.log(`Checking pane ${pIdx}...`);
            const out = execSync(`tmux capture-pane -t tom_hum:brain.${pIdx} -p -S -30 2>/dev/null`, { encoding: 'utf-8' });
            const res = await interpretState(out);
            console.log(`P${pIdx} State:`, res);
        } catch (e) {
            console.error(`P${pIdx} error:`, e.message);
        }
    }
}
test();
