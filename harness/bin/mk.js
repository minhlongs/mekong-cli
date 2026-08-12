#!/usr/bin/env node
/**
 * Mekong CLI Entry Point
 * Loads harness core with Mekong persona
 */

import { Harness } from '../src/index';
import { MekongPersona } from '../src/personas/mekong-persona';
import * as path from 'path';
import * as fs from 'fs';

// Determine config root
const configRoot = process.env.MEKONG_ROOT || path.join(process.env.HOME || '', 'mekong-cli');

async function main() {
  const args = process.argv.slice(2);
  
  // Parse global options
  let model = 'claude-opus-4-8';
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

  // Create harness with Mekong persona
  const harness = new Harness({
    configRoot,
    persona: 'mekong',
    model,
    debug,
  });

  // Handle shutdown gracefully
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
