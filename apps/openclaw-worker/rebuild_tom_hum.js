const { spawnBrain } = require('./lib/brain-process-manager');
(async () => {
    console.log("Spawning PRO window...");
    await spawnBrain(1, 'PLAN');
    console.log("Spawning API window...");
    await spawnBrain(1, 'EXECUTION');
    console.log("Rebuild complete.");
    process.exit(0);
})();
