const { spawnBrain } = require('./lib/brain-process-manager');
(async () => {
    console.log("Nuclear Restart: Building PRO...");
    await spawnBrain(1, 'PLAN');
    console.log("Nuclear Restart: Building API...");
    await spawnBrain(1, 'EXECUTION');
    console.log("Dual tabs established.");
    process.exit(0);
})();
