/**
 * AGI SOPs - Entry Point
 */

import Orchestrator from './orchestrator.js';

// Create orchestrator instance
const orchestrator = new Orchestrator({
  model: process.env.LLM_MODEL || 'llama3.2',
  host: process.env.OLLAMA_HOST || 'http://127.0.0.1:11434'
});

// Example SOP: Content Research
const contentResearchSOP = {
  name: 'content-research',
  version: '1.0.0',
  description: 'Research topic and generate content outline',
  steps: [
    {
      id: 'research',
      name: 'Research Topic',
      action: 'llm:chat',
      prompt: 'Research the following topic and provide key insights:',
      params: {
        topic: '{{topic}}'
      }
    },
    {
      id: 'outline',
      name: 'Generate Outline',
      action: 'llm:chat',
      prompt: 'Create a detailed outline based on the research:',
      params: {
        research: '{{research.result}}'
      }
    },
    {
      id: 'save',
      name: 'Save Outline',
      action: 'file:write',
      params: {
        path: './output/outline.md',
        content: '{{outline.result}}'
      }
    }
  ]
};

// Main execution
async function main() {
  console.log('🤖 AGI SOPs Engine Starting...\n');

  // Load example SOP
  await orchestrator.loadSOP('content-research', contentResearchSOP);

  // Execute with context
  const result = await orchestrator.execute('content-research', {
    topic: 'Local LLM Automation'
  });

  console.log('\n✅ SOP Execution Complete:');
  console.log(`Status: ${result.status}`);
  console.log(`Duration: ${result.duration}ms`);
  console.log(`Steps: ${result.steps.length}`);
}

// Handle errors
main().catch(error => {
  console.error('❌ Fatal Error:', error.message);
  process.exit(1);
});
