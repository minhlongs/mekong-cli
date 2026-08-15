/**
 * roiaas-chain.ts — ROIaaS Delegation Chain Validator
 * Validates the full command hierarchy: studio → cto → pm → dev → worker
 */
import { ROIAAS_LEVELS } from './gateway.js';
import type { RoiaasLevel } from './gateway.js';
import { readFileSync, existsSync } from 'fs';
import { join } from 'path';

export interface ChainValidation {
  level: RoiaasLevel;
  command: string;
  hasClaudeCommand: boolean;
  hasContract: boolean;
  hasRecipe: boolean;
  delegatesTo: string[];
}

export interface ChainReport {
  valid: boolean;
  totalCommands: number;
  missingClaudeCommands: string[];
  missingContracts: string[];
  missingRecipes: string[];
  delegationChain: string;
  validations: ChainValidation[];
}

/**
 * Validate the full ROIaaS command stack against the filesystem.
 * Checks that every command in layers.json has matching Claude command, contract, and recipe.
 */
export function validateChain(projectRoot: string): ChainReport {
  const layersPath = join(projectRoot, 'factory', 'contracts', 'layers.json');
  if (!existsSync(layersPath)) {
    return {
      valid: false,
      totalCommands: 0,
      missingClaudeCommands: [],
      missingContracts: [],
      missingRecipes: [],
      delegationChain: 'MISSING layers.json',
      validations: [],
    };
  }

  const layers = JSON.parse(readFileSync(layersPath, 'utf-8'));
  const validations: ChainValidation[] = [];
  const missingClaudeCommands: string[] = [];
  const missingContracts: string[] = [];
  const missingRecipes: string[] = [];

  const roiaasLevels: RoiaasLevel[] = ['studio', 'cto', 'pm', 'dev', 'worker'];

  for (const level of roiaasLevels) {
    const layerDef = layers.layers[level];
    if (!layerDef) continue;

    for (const cmd of layerDef.commands) {
      const claudeCmdPath = join(projectRoot, '.claude', 'commands', `${cmd}.md`);
      const contractPath = join(projectRoot, 'factory', 'contracts', 'commands', `${cmd}.json`);
      const recipeName = cmd.replace(`${level}-`, '');
      const recipePath = join(projectRoot, 'recipes', level, `${recipeName}.json`);

      const hasClaudeCommand = existsSync(claudeCmdPath);
      const hasContract = existsSync(contractPath);
      // Workers don't need recipes (atomic execution)
      const hasRecipe = level === 'worker' ? true : existsSync(recipePath);

      if (!hasClaudeCommand) missingClaudeCommands.push(cmd);
      if (!hasContract) missingContracts.push(cmd);
      if (!hasRecipe && level !== 'worker') missingRecipes.push(cmd);

      // Parse delegation targets from contract if available
      let delegatesTo: string[] = [];
      if (hasContract) {
        try {
          const contract = JSON.parse(readFileSync(contractPath, 'utf-8'));
          delegatesTo = contract.cascade?.triggers || [];
        } catch { /* ignore parse errors */ }
      }

      validations.push({
        level,
        command: cmd,
        hasClaudeCommand,
        hasContract,
        hasRecipe,
        delegatesTo,
      });
    }
  }

  const chain = roiaasLevels
    .map(l => `${ROIAAS_LEVELS[l].icon} ${l}`)
    .join(' → ');

  return {
    valid: missingClaudeCommands.length === 0 && missingContracts.length === 0 && missingRecipes.length === 0,
    totalCommands: validations.length,
    missingClaudeCommands,
    missingContracts,
    missingRecipes,
    delegationChain: chain,
    validations,
  };
}

/**
 * Print a human-readable chain validation report.
 */
export function printChainReport(report: ChainReport): string {
  const lines: string[] = [
    '═══ ROIaaS Command Stack Validation ═══',
    '',
    `Chain: ${report.delegationChain}`,
    `Total: ${report.totalCommands} commands`,
    `Status: ${report.valid ? '✅ VALID' : '❌ INCOMPLETE'}`,
    '',
  ];

  if (report.missingClaudeCommands.length > 0) {
    lines.push(`Missing Claude Commands (${report.missingClaudeCommands.length}):`);
    for (const cmd of report.missingClaudeCommands) {
      lines.push(`  - .claude/commands/${cmd}.md`);
    }
    lines.push('');
  }

  if (report.missingContracts.length > 0) {
    lines.push(`Missing Contracts (${report.missingContracts.length}):`);
    for (const cmd of report.missingContracts) {
      lines.push(`  - factory/contracts/commands/${cmd}.json`);
    }
    lines.push('');
  }

  if (report.missingRecipes.length > 0) {
    lines.push(`Missing Recipes (${report.missingRecipes.length}):`);
    for (const cmd of report.missingRecipes) {
      lines.push(`  - recipes/${cmd.split('-')[0]}/${cmd}.json`);
    }
    lines.push('');
  }

  // Per-level summary
  const levels: RoiaasLevel[] = ['studio', 'cto', 'pm', 'dev', 'worker'];
  for (const level of levels) {
    const cmds = report.validations.filter(v => v.level === level);
    const complete = cmds.filter(v => v.hasClaudeCommand && v.hasContract && v.hasRecipe).length;
    lines.push(`${ROIAAS_LEVELS[level].icon} ${level}: ${complete}/${cmds.length} complete`);
  }

  return lines.join('\n');
}
