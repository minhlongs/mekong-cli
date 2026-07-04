/**
 * `mekong cook` — Run recipes with platform filtering.
 *
 *   mekong cook                      Run all recipes (general only by default)
 *   mekong cook --platform cloudflare Run only Cloudflare recipes
 *   mekong cook <recipe-name>         Run specific recipe
 *   mekong cook <recipe> --platform cloudflare  Run specific recipe with platform filter
 *
 * Options:
 *   --platform <platform>   Filter recipes by platform (cloudflare|vercel|netlify|general)
 *   --recipes-dir <dir>     Custom recipes directory path
 */

import type { Command } from 'commander';
import { heading, info, warn, success, error as cliError, divider, keyValue } from '../ui/output.js';
import { cook, formatCookSummary } from '../../recipe-runner.js';

export function registerCookCommand(program: Command): void {
  const cmd = program.command('cook').description('Run recipes with platform filtering');
  
  // Optional recipe name argument
  cmd.argument('[recipe]', 'Optional recipe name to run');
  
  // Platform option
  cmd.option('--platform <platform>', 'Filter by platform (cloudflare|vercel|netlify|general)');
  
  // Custom recipes directory
  cmd.option('--recipes-dir <dir>', 'Custom recipes directory path');
  
  cmd.action(async (recipeName: string | undefined, opts: { platform?: string; recipesDir?: string }) => {
    heading('Mekong Cook');
    
    try {
      const summary = await cook({
        platform: opts.platform,
        recipeName,
        recipesDir: opts.recipesDir,
      });
      
      divider();
      console.log(formatCookSummary(summary));
      
      if (summary.results.every(r => r.status === 'success')) {
        success('All recipes completed successfully');
      } else {
        const failed = summary.results.filter(r => r.status === 'failed');
        if (failed.length > 0) {
          warn(`${failed.length} recipe(s) failed`);
        }
      }
    } catch (err: any) {
      cliError(`Cook failed: ${err.message}`);
      process.exit(1);
    }
  });
}
