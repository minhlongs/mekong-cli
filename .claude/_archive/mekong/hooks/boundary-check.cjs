#!/usr/bin/env node
/**
 * boundary-check.cjs — Check file access against zone map
 * Warns if agent tries to write to QUAN DOANH without approval
 */
'use strict';

// Zone map
const ZONES = {
  'quan_doanh': [
    'mekong/bootstrap/', 'mekong/init/', 'mekong/audit/',
    'mekong/constitution/', 'mekong/hooks/',
    '.claude/hooks/', '.ck.json'
  ],
  'doanh_trai': [
    '.claude/commands/', '.claude/skills/', '.claude/agents/',
    'workflows/', 'docs/'
  ],
  'kho_luong': [
    'build/', 'dist/', '.pytest_cache/', '.ruff_cache/',
    '__pycache__/'
  ],
  'hanh_lang': [
    '.agent/', '.agents/', '.antigravity/', '.gemini/',
    '.opencode/', '.cursorrules/', '.claude-backup/', '.claude-skills/'
  ]
};

// Check user prompt for file modification paths
const prompt = process.argv[2] || '';
for (const [zone, paths] of Object.entries(ZONES)) {
  for (const p of paths) {
    if (prompt.includes(p)) {
      if (zone === 'quan_doanh') {
        process.stdout.write(`\n⚠️  ⚔️ QUAN DOANH DETECTED: ${p} — Read-only zone. Can /binh-phap win de sua.\n`);
      } else if (zone === 'hanh_lang') {
        process.stdout.write(`\n⚠️  HÀNH LANG: ${p} — Orphan dir. Không tạo file mới ở đày.\n`);
      }
    }
  }
}
