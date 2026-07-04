#!/usr/bin/env node
/**
 * military-law-inject.cjs — Inject Binh Phap Quân Luật vào session context
 * Runs on SessionStart hook. Writes zone map + 5 điều luật to stdout.
 */
'use strict';
var ctx = '';
ctx += '\n=== ⚔️ BINH PHAP QUÂN LUẬT ===\n';
ctx += 'ZONES:\n';
ctx += '  QUÂN DOANH (read-only): mekong/, .claude/hooks/, constitution/, .ck.json\n';
ctx += '  DOANH TRẠI (read-write): .claude/commands/, .claude/skills/, workflows/\n';
ctx += '  KHO LƯƠNG (temp): build/, dist/, caches (git-ignored)\n';
ctx += '  HÀNH LANG (orphan): .agent/, .agents/, .antigravity/ (archive)\n';
ctx += '\n';
ctx += '⚔️ 5 ĐIỀU LUẬT:\n';
ctx += '  1. KHÔNG sửa QUÂN DOANH không có /binh-phap win\n';
ctx += '  2. KHÔNG tạo file mới ở root — vào đúng phân khu\n';
ctx += '  3. KHÔNG duplicate skill/command — audit trước khi tạo\n';
ctx += '  4. KHÔNG commit rác (reports, caches, orphans)\n';
ctx += '  5. PHẢI chạy `mekong audit --military` trước khi kết thúc phiên\n';
ctx += '=== ⚔️ ===\n';
process.stdout.write(ctx);
