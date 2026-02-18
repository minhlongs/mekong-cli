const { PerceptionDashboard } = require('./dist');
const path = require('path');

async function main() {
  const rootDir = path.resolve(__dirname, '../../..');
  const logDir = path.join(rootDir, 'logs');
  const pidFile = path.join(rootDir, 'brain_pid.txt');
  
  console.log('--- Testing Perception Dashboard ---');
  console.log('Root:', rootDir);

  const dashboard = new PerceptionDashboard(rootDir, logDir, pidFile);
  
  try {
    const report = await dashboard.generateReport();
    console.log('\n--- Dashboard Summary ---');
    console.log(JSON.stringify(report.summary, null, 2));
    
    console.log('\n--- Service Status ---');
    console.log(report.serviceStatus);

    console.log('\n--- Top 3 Projects by Tech Debt (Any Type) ---');
    const sorted = [...report.projects].sort((a, b) => b.techDebt.anyCount - a.techDebt.anyCount);
    sorted.slice(0, 3).forEach(p => {
        console.log(`${p.name}: ${p.techDebt.anyCount} any types`);
    });

    if (report.projects.length > 0) {
        console.log('\n✅ Dashboard generation successful');
    }
  } catch (e) {
    console.error('❌ Dashboard generation failed:', e);
  }
}

main().catch(console.error);
