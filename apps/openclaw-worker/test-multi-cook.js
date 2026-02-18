/**
 * Test script để verify buildPrompt() chaining nhiều /cook commands
 */

const { buildPrompt } = require('./lib/mission-dispatcher');

console.log('=== TEST 1: Short simple task (should NOT chain) ===');
const simple = buildPrompt('Fix login bug');
console.log('OUTPUT:');
console.log(simple);
const cookCount1 = (simple.match(/\/cook/g) || []).length;
console.log(`\n✅ /cook count: ${cookCount1} (expected: 1)\n\n`);

console.log('=== TEST 2: Long task with separators (SHOULD chain) ===');
const complex = buildPrompt('Fix broken routes and sync prices và update docs; add new feature for payment và verify production GREEN');
console.log('OUTPUT:');
console.log(complex);
const cookCount2 = (complex.match(/\/cook/g) || []).length;
console.log(`\n✅ /cook count: ${cookCount2} (expected: >= 2)\n\n`);

console.log('=== TEST 3: Long task with multiple sentences (SHOULD chain) ===');
const multiSentence = buildPrompt('Update authentication system to use OAuth2. Add rate limiting to API endpoints. Fix security vulnerabilities in user input validation. Deploy to production.');
console.log('OUTPUT:');
console.log(multiSentence);
const cookCount3 = (multiSentence.match(/\/cook/g) || []).length;
console.log(`\n✅ /cook count: ${cookCount3} (expected: >= 2)\n\n`);

console.log('=== TEST 4: Task with "and" separator ===');
const andSeparator = buildPrompt('Fix authentication and add payment integration and update documentation and run tests');
console.log('OUTPUT:');
console.log(andSeparator);
const cookCount4 = (andSeparator.match(/\/cook/g) || []).length;
console.log(`\n✅ /cook count: ${cookCount4} (expected: >= 2)\n\n`);

console.log('=== SUMMARY ===');
console.log(`Test 1 (simple): ${cookCount1} /cook (expected: 1) — ${cookCount1 === 1 ? '✅ PASS' : '❌ FAIL'}`);
console.log(`Test 2 (complex): ${cookCount2} /cook (expected: >= 2) — ${cookCount2 >= 2 ? '✅ PASS' : '❌ FAIL'}`);
console.log(`Test 3 (sentences): ${cookCount3} /cook (expected: >= 2) — ${cookCount3 >= 2 ? '✅ PASS' : '❌ FAIL'}`);
console.log(`Test 4 (and): ${cookCount4} /cook (expected: >= 2) — ${cookCount4 >= 2 ? '✅ PASS' : '❌ FAIL'}`);

const allPass = (cookCount1 === 1) && (cookCount2 >= 2) && (cookCount3 >= 2) && (cookCount4 >= 2);
console.log(`\n${allPass ? '🎉 ALL TESTS PASSED' : '⚠️ SOME TESTS FAILED'}`);
process.exit(allPass ? 0 : 1);
