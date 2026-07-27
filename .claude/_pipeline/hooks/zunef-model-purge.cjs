#!/usr/bin/env node
// ZuneF Model Purge Hook
// Fires: SessionStart — after picker or startup may have written Anthropic presets
// Purpose: Scan settings.json, replace any Anthropic presets with ZuneF equivalents
try {
  const fs = require('fs');
  const os = require('os');
  const path = require('path');

  const SETTINGS = process.env.CLAUDE_PROJECT_DIR
    ? path.join(process.env.CLAUDE_PROJECT_DIR, '.claude', 'settings.json')
    : path.join(os.homedir(), '.claude', 'settings.json');

  const PRESETS = ['opus', 'sonnet', 'haiku', 'claude-5', 'opus-5', 'sonnet-5', 'haiku-4.5', 'opus[1m]', 'sonnet[1m]'];
  const MAP = {
    'opus': 'claude-opus-4-8',
    'sonnet': 'claude-fable-5',
    'haiku': 'claude-haiku-4-5',
    'claude-5': 'claude-fable-5',
    'opus-5': 'claude-opus-4-8',
    'sonnet-5': 'claude-sonnet-5-0',
    'haiku-4.5': 'claude-haiku-4-5',
    'opus[1m]': 'claude-opus-4-6[1m]',
    'sonnet[1m]': 'claude-opus-4-6[1m]'
  };

  function purge(d) {
    let fixed = 0;
    if (!d || typeof d !== 'object') return fixed;
    for (const k of ['model', 'defaultModel']) {
      if (d[k] && typeof d[k] === 'string') {
        const v = d[k];
        for (const p of PRESETS) {
          if (v === p || v.toLowerCase().startsWith(p)) {
            d[k] = MAP[p] || 'claude-fable-5';
            console.error(`[zunef-purge] fixed ${k}: ${v} -> ${d[k]}`);
            fixed++;
            break;
          }
        }
      }
    }
    // modelRouting.providers — ensure no direct Anthropic
    if (d.modelRouting && d.modelRouting.providers) {
      const ap = d.modelRouting.providers.anthropic;
      if (ap) {
        console.error('[zunef-purge] removed anthropic provider from routing, using zunef');
        delete d.modelRouting.providers.anthropic;
        fixed++;
      }
    }
    return fixed;
  }

  if (!fs.existsSync(SETTINGS)) process.exit(0);
  const raw = fs.readFileSync(SETTINGS, 'utf8');
  const cfg = JSON.parse(raw);
  const fixed = purge(cfg);
  if (fixed > 0) {
    fs.writeFileSync(SETTINGS, JSON.stringify(cfg, null, 2) + '\n');
    console.error(`[zunef-purge] ${fixed} fix(es) applied`);
  }
} catch (e) {
  console.error('[zunef-purge] error:', e.message);
}
process.exit(0);
