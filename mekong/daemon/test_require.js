
try {
  console.log('Attempting to require lib/post-mission-gate.js...');
  require('./lib/post-mission-gate.js');
  console.log('Successfully required lib/post-mission-gate.js');

  console.log('Attempting to require lib/mission-journal.js...');
  require('./lib/mission-journal.js');
  console.log('Successfully required lib/mission-journal.js');

  process.exit(0);
} catch (error) {
  console.error('Failed to load module:', error.message);
  process.exit(1);
}
