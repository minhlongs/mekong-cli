const { spawnBrain } = require('./lib/brain-process-manager');
const { execSync } = require('child_process');
(async () => {
    console.log("Building Window 0 (pro)...");
    await spawnBrain(1, 'PLAN');
    console.log("Building Window 1 (api)...");
    // Force Window 1 manually since spawnBrain logic might collide if intent varies
    try {
        execSync(`tmux new-window -t tom_hum -n api -c /Users/macbookprom1/mekong-cli`);
    } catch(e) {}
    await spawnBrain(1, 'EXECUTION');
    console.log("Dual tabs established.");
    process.exit(0);
})();
