export const meta = {
  name: 'zenos-full-redesign',
  description: 'Redesign mekong-cli to ZenOS constitution with 10 phases in parallel where possible',
  phases: [
    {title: 'Audit', detail: 'Check current state'},
    {title: 'Parallel Build', detail: 'Phases 1-7 core systems'},
    {title: 'Migration', detail: 'Phase 8 - Tenant→Particle'},
    {title: 'Tests & Docs', detail: 'Phases 9-10'},
    {title: 'Integration', detail: 'Final check'},
  ],
};

phase('Audit');
const state = await agent('Audit current project: list plans/, check DB config (docker-compose), read src/models/, list existing CLI commands, check if Neo4j/Redis/Qdrant running. Return concise status with file paths and key findings.', {
  label: 'audit-current-state',
  schema: {
    type: 'object',
    properties: {
      plansDir: { type: 'string' },
      existingPlan: { type: 'boolean' },
      dbConfig: { type: 'string' },
      modelsPath: { type: 'string' },
      cliCommands: { type: 'array', items: {type: 'string'} },
      graphDb: { type: 'string' },
      redisRunning: { type: 'boolean' },
      mekongConfig: { type: 'object' },
    },
  },
});
log(`Audit complete: ${state.existingPlan ? 'plan exists' : 'no plan'}, DB: ${state.dbConfig}`);

phase('Parallel Build');
// Core phases 1-7 are file-isolated, run in parallel
const [db, constitution, genome, graph, zenpay, governance, cli] = await parallel([
  () => agent('Design Economic Particle DB schema: 1) Create migration file for PostgreSQL, 2) Create models/particle.py ORM, 3) Refactor raas/tenant.py to particle.py, 4) Ensure Vietnam compatibility. Return: file paths, SQL, ORM classes.', {
    label: 'phase1-db',
    schema: { type: 'object', properties: { migrationFile: {type:'string'}, modelFile: {type:'string'}, raasRefactor: {type:'string'}, sqlStatements: {type:'array', items:{type:'string'}} } },
  }),
  () => agent('Implement Constitutional AI middleware: 1) src/core/constitution.py with 9 principles + review(), 2) src/api/middleware.py ConstitutionalReview, 3) Integrate into src/core/orchestrator.py PEV engine hooks, 4) Add constitutional_score metric. Return: file paths, review logic code.', {
    label: 'phase2-constitution',
    schema: { type: 'object', properties: { constitutionFile: {type:'string'}, middlewareFile: {type:'string'}, orchestratorMod: {type:'string'}, reviewLogic: {type:'string'} } },
  }),
  () => agent('Create Founder Genome capture: 1) src/cli/genome_command.py with mekong genome init wizard, 2) src/services/genome_service.py for storage/encryption, 3) AI analysis prompts, 4) table founder_genomes. Return: command, service, encryption, prompts.', {
    label: 'phase3-genome',
    schema: { type: 'object', properties: { cliFile: {type:'string'}, serviceFile: {type:'string'}, prompts: {type:'array', items:{type:'string'}}, tableSql: {type:'string'} } },
  }),
  () => agent('Implement Behavior Graph Service: 1) Choose storage (Neo4j else PostgreSQL JSONB), 2) src/graph/schema.py, 3) src/graph/service.py, 4) GraphRAG integration. Return: choice, schema, service, hook.', {
    label: 'phase4-graph',
    schema: { type: 'object', properties: { storageChoice: {type:'string'}, schemaFile: {type:'string'}, serviceFile: {type:'string'}, graphragHook: {type:'string'} } },
  }),
  () => agent('Build ZenPay Money OS: 1) src/zenpay/ package with Stripe/Wise, 2) Multi-currency treasury (VND,USD,USDT), 3) Self-custody option, 4) API endpoints, 5) Compliance. Return: files, provider, APIs, currencies.', {
    label: 'phase5-zenpay',
    schema: { type: 'object', properties: { packagePath: {type:'string'}, provider: {type:'string'}, apiEndpoints: {type:'array', items:{type:'string'}}, currencies: {type:'array', items:{type:'string'}} } },
  }),
  () => agent('Create Ostrom Governance Framework: 1) src/governance/amendment.py, 2) voting.py (reputation-weighted), 3) sanctions.py, 4) dispute.py. Return: files, algorithm, flow.', {
    label: 'phase6-governance',
    schema: { type: 'object', properties: { amendmentFile: {type:'string'}, votingFile: {type:'string'}, sanctionsFile: {type:'string'}, disputeFile: {type:'string'}, flowDesc: {type:'string'} } },
  }),
  () => agent('Refactor CLI to particle-first: 1) src/cli/particle_command.py, 2) constitution_command.py, 3) Update all CLI to use particle_id, 4) Keep Vietnam commands. Return: new files, updated commands, backwards compat plan.', {
    label: 'phase7-cli',
    schema: { type: 'object', properties: { particleCmdFile: {type:'string'}, constitutionCmdFile: {type:'string'}, updatedCommands: {type:'array', items:{type:'string'}}, backwardsCompat: {type:'string'} } },
  }),
]);
log(`Core phases complete: DB=${!!db}, Const=${!!constitution}, Genome=${!!genome}, Graph=${!!graph}, ZenPay=${!!zenpay}, Gov=${!!governance}, CLI=${!!cli}`);

phase('Migration');
const migrationResult = await agent('Create migration script: scripts/migrate-tenants-to-particles.py with 1) tenants→particles copy, 2) constitution init, 3) empty behavior_graph, 4) empty treasury, 5) backwards compat flag. Return: script, test cmd, rollback.', {
  label: 'phase8-migration',
  schema: { type: 'object', properties: { scriptFile: {type:'string'}, testCmd: {type:'string'}, rollbackPlan: {type:'string'} } },
});

phase('Tests & Docs');
// Tests and docs can run parallel
const [testResult, docsResult] = await parallel([
  () => agent('Write tests: tests/zenos/ with particle lifecycle, Constitutional AI review, Vietnam regression tests. Return: files, coverage target.', {
    label: 'phase9-tests',
    schema: { type: 'object', properties: { testFiles: {type:'array', items:{type:'string'}}, coverageTarget: {type:'number'} } },
  }),
  () => agent('Write documentation: migration guide, economic particles, constitutional AI, founder genome, update README. Return: files, key sections.', {
    label: 'phase10-docs',
    schema: { type: 'object', properties: { docFiles: {type:'array', items:{type:'string'}}, readmeUpdated: {type:'boolean'} } },
  }),
]);

phase('Integration');
const integrationAgent = agent('Perform integration check: 1) Import all new modules, 2) Verify particle_id replaces org_id, 3) Check Constitutional middleware active, 4) Verify Behavior Graph queries, 5) Run sample migration on test DB. Return: pass/fail, issues.', {
  label: 'integration-check',
  schema: {
    type: 'object',
    properties: {
      status: { type: 'string', enum: ['PASS', 'FAIL', 'CONCERNS'] },
      issues: { type: 'array', items: {type: 'string'} },
      importErrors: { type: 'array', items: {type: 'string'} },
    },
  },
});

return {
  audit: state,
  phases: { db, constitution, genome, graph, zenpay, governance, cli, migration: migrationResult, tests: testResult, docs: docsResult, integration: integrationAgent },
  summary: `ZenOS redesign complete. ${integrationAgent.status === 'PASS' ? 'All systems ready' : 'Review issues'}`,
};