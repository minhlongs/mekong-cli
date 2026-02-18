const { MonorepoIndexer, HealthMonitor, ImpactAnalyzer, SessionMemory } = require('./dist');
const path = require('path');

async function main() {
  const rootDir = path.resolve(__dirname, '../../..');
  console.log('Root dir:', rootDir);

  // 1. Test Indexer
  console.log('\n--- Testing Indexer ---');
  const indexer = new MonorepoIndexer(rootDir);
  try {
    const graph = await indexer.scan();
    console.log('Nodes found:', Object.keys(graph.nodes).length);
    console.log('Edges found:', graph.edges.length);
    if (Object.keys(graph.nodes).length > 0) {
        console.log('✅ Indexer working');
    }
  } catch (e) {
    console.error('❌ Indexer failed:', e);
  }

  // 2. Test Impact Analyzer
  console.log('\n--- Testing Impact Analyzer ---');
  const analyzer = new ImpactAnalyzer(rootDir);
  const changedFile = path.join(rootDir, 'packages/core/shared/index.ts');
  try {
    const impacted = await analyzer.analyze([changedFile]);
    console.log('Changed file:', changedFile);
    console.log('Impacted packages:', impacted);
    if (impacted.includes('@mekong/shared')) {
         console.log('✅ Impact analyzer detected direct impact');
    }
  } catch (e) {
    console.error('❌ Impact Analyzer failed:', e);
  }

  // 3. Test Session Memory
  console.log('\n--- Testing Session Memory ---');
  const memoryDir = path.join(rootDir, '.mekong/memory');
  const memory = new SessionMemory(memoryDir);
  try {
    await memory.initSession('test-session');
    await memory.addShortTerm('User: Hello world');
    await memory.setFact('theme', 'dark');
    const fact = await memory.getFact('theme');
    console.log('Fact retrieved:', fact);
    if (fact === 'dark') {
        console.log('✅ Session Memory working');
    }
  } catch (e) {
    console.error('❌ Session Memory failed:', e);
  }

  // 4. Test Health Monitor
  console.log('\n--- Testing Health Monitor ---');
  const logDir = path.join(rootDir, 'logs');
  const pidFile = path.join(rootDir, 'brain_pid.txt');
  const monitor = new HealthMonitor(logDir, pidFile);
  try {
    const status = await monitor.checkOpenClawStatus();
    console.log('OpenClaw Status:', status);
    
    // Test Project Health
    const perceptionPath = path.resolve(__dirname);
    console.log('Checking project health for:', perceptionPath);
    const projectHealth = await monitor.checkProjectHealth(perceptionPath);
    console.log('Project Health:', JSON.stringify(projectHealth, null, 2));
    
    if (projectHealth.name === '@mekong/perception' && projectHealth.techDebt) {
        console.log('✅ Health Monitor (Project Check) working');
    }
  } catch (e) {
    console.error('❌ Health Monitor failed:', e);
  }
}

main().catch(console.error);
