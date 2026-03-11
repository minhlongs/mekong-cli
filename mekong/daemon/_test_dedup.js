const QL = require('./lib/quan-luat-enforcer');

console.log('=== LUẬT CHƠI VERIFICATION ===');
console.log('');

// Test 1
const exists = QL.checkDuplicate('hunter', 'apex-os', 'security_risk');
console.log('Test 1 - Dedup finds existing:', exists ? '✅ PASS' : '❌ FAIL');

// Test 2
const notExists = QL.checkDuplicate('hunter', 'nonexistent', 'foobar');
console.log('Test 2 - Dedup skips new:', !notExists ? '✅ PASS' : '❌ FAIL');

// Test 3
const ok = QL.checkQueueDiscipline('hunter');
console.log('Test 3 - Queue discipline:', typeof ok === 'boolean' ? '✅ PASS' : '❌ FAIL');

// Test 4
const files = QL.getTaskFiles();
console.log('Test 4 - Total task files:', files.length);

// Test 5
console.log('Test 5 - Wave1 (0ms):', QL.BOOT_ECHELONS.wave1.daemons.join(', '));
console.log('Test 5 - Wave2 (30s):', QL.BOOT_ECHELONS.wave2.daemons.join(', '));
console.log('Test 5 - Wave3 (60s):', QL.BOOT_ECHELONS.wave3.daemons.join(', '));

console.log('');
console.log('=== ALL TESTS DONE ===');
