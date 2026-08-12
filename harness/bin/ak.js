#!/usr/bin/env node
/**
 * Agent Kit CLI Entry Point
 * Loads harness core with Agent Kit persona
 */

import { Harness } from '../src/index';
import { AgentKitPersona } from '../src/personas/agentkit-persona';
import * as path from 'path';

const configRoot = process.env.MEKONG_ROOT || path.join(process.env.HOME || '', 'mekong-cli');

async function main() {
  const args = process.argv.slice(2);
  
  let model = 'claude-fable-5';
  let debug = false;
  const commandArgs: string[] = [];
  
  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--model' && i + 1 < args.length) {
      model = args[++i];
    } else if (args[i] === '--debug') {
      debug = true;
    } else if (args[i] === '--help' || args[i] === '-h') {
      commandArgs.push('help');
    } else {
      commandArgs.push(args[i]);
    }
  }

  const harness = new Harness({
    configRoot,
    persona: 'agentkit',
    model,
    debug,
  });

  process.on('SIGINT', async () => {
    console.log('\n[Harness] Shutting down...');
    await harness.shutdown();
    process.exit(0);
  });

  process.on('SIGTERM', async () => {
    await harness.shutdown();
    process.exit(0);
  });

  try {
    await harness.run(commandArgs);
  } catch (error) {
    console.error('[Harness] Error:', error instanceof Error ? error.message : error);
    process.exit(1);
  }
}

main();
