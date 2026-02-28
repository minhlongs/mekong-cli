/**
 * Test script for vector-service.js
 */
const vectorService = require('./lib/vector-service');

async function test() {
  console.log('--- Testing Vector Service ---');

  try {
    // 1. Test Embedding
    console.log('Testing getEmbedding...');
    const vector = await vectorService.getEmbedding('Hello world, I am Tôm Hùm AGI Level 9.');
    console.log('Vector generated successfully. Length:', vector.length);
    console.log('First 5 values:', vector.slice(0, 5));

    // 2. Test Upsert
    console.log('\nTesting upsert...');
    const testData = [
      { text: 'Sun Tzu said: All warfare is based on deception.', author: 'Sun Tzu', type: 'philosophy' },
      { text: 'The supreme art of war is to subdue the enemy without fighting.', author: 'Sun Tzu', type: 'philosophy' },
      { text: 'Mekong-CLI is a powerful agentic framework.', type: 'technical' }
    ];
    await vectorService.upsert('test_table', testData);
    console.log('Upsert successful.');

    // 3. Test Search
    console.log('\nTesting search...');
    const results = await vectorService.search('test_table', 'warfare and deception');
    console.log('Search results for "warfare and deception":');
    results.forEach((r, i) => {
      console.log(`${i+1}. [Score: ${r._distance.toFixed(4)}] ${r.text}`);
    });

    // 4. Test Search with Filter
    console.log('\nTesting search with filter (type = "technical")...');
    const filteredResults = await vectorService.search('test_table', 'framework', 'type = "technical"');
    console.log('Filtered search results:');
    filteredResults.forEach((r, i) => {
      console.log(`${i+1}. [Score: ${r._distance.toFixed(4)}] ${r.text}`);
    });

    console.log('\n--- All Tests Passed ---');
  } catch (error) {
    console.error('\n!!! Test Failed !!!');
    console.error(error);
    process.exit(1);
  }
}

test();
