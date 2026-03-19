// @mekong/openclaw-engine — re-exports all domains
'use strict';

// core
exports.brainStateMachine = require('./src/core/brain-state-machine');
exports.brainBootSequence = require('./src/core/brain-boot-sequence');
exports.brainSpawnManager = require('./src/core/brain-spawn-manager');
exports.brainMissionRunner = require('./src/core/brain-mission-runner');
exports.brainRespawnController = require('./src/core/brain-respawn-controller');
exports.brainTerminalApp = require('./src/core/brain-terminal-app');
exports.brainProcessManager = require('./src/core/brain-process-manager');

// orchestration
exports.autoCtoPilot = require('./src/orchestration/auto-cto-pilot');
exports.ctoTaskDispatch = require('./src/orchestration/cto-task-dispatch');
exports.ctoPaneHandler = require('./src/orchestration/cto-pane-handler');
exports.missionDispatcher = require('./src/orchestration/mission-dispatcher');
exports.ctoPaneStateDetector = require('./src/orchestration/cto-pane-state-detector');
exports.ctoTmuxHelpers = require('./src/orchestration/cto-tmux-helpers');

// reliability
exports.circuitBreaker = require('./src/reliability/circuit-breaker');
exports.brainHeartbeat = require('./src/reliability/brain-heartbeat');
exports.brainOutputHashStagnationWatchdog = require('./src/reliability/brain-output-hash-stagnation-watchdog');
exports.missionRecovery = require('./src/reliability/mission-recovery');
exports.brainSystemMonitor = require('./src/reliability/brain-system-monitor');

// intelligence
exports.learningEngine = require('./src/intelligence/learning-engine');
exports.evolutionEngine = require('./src/intelligence/evolution-engine');
exports.missionComplexityClassifier = require('./src/intelligence/mission-complexity-classifier');
exports.postMissionGate = require('./src/intelligence/post-mission-gate');
exports.projectScanner = require('./src/intelligence/project-scanner');

// observability
exports.brainHealthServer = require('./src/observability/brain-health-server');
exports.agiScoreCalculator = require('./src/observability/agi-score-calculator');
exports.apiRateGate = require('./src/observability/api-rate-gate');
exports.missionJournal = require('./src/observability/mission-journal');

// safety
exports.safetyGuard = require('./src/safety/safety-guard');
exports.m1CoolingDaemon = require('./src/safety/m1-cooling-daemon');
exports.resourceGovernor = require('./src/safety/resource-governor');
exports.selfHealer = require('./src/safety/self-healer');

// raas (ROIaaS-as-a-Service)
exports.raas = require('./src/raas/index');

