const { spawnBrain } = require('./lib/brain-process-manager');
(async () => {
    console.log("Building Window 0 (PRO)...");
    await spawnBrain(1, 'PLAN');
    console.log("Building Window 1 (API)...");
    await spawnBrain(1, 'EXECUTION');
    console.log("Dual tabs built.");
    process.exit(0);
})();
