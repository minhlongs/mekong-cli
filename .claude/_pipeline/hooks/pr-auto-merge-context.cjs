#!/usr/bin/env node
/**
 * pr-auto-merge-context.cjs — Inject auto-merge rules vào mọi session
 * AI đọc cái này là biết PR muốn merge phải làm gì.
 */
'use strict';
var ctx = '';
ctx += '\n=== 🔀 AUTO-MERGE RULES ===\n';
ctx += 'Có PR cần merge? KHÔNG hỏi founder. TỰ XỬ LÝ:\n';
ctx += '  1. Label PR = auto-merge\n';
ctx += '  2. Tự resolve conflict (accept ours nếu benign)\n';
ctx += '  3. Tự merge: gh pr merge <pr> --squash --admin\n';
ctx += '  4. Tự restore branch protection sau merge\n';
ctx += '  5. Chỉ báo founder khi merge FAILED hoặc conflict ko resolve được\n';
ctx += 'Cách chạy nhanh: node scripts/auto-merge.cjs <pr-url> --admin\n';
ctx += 'Docs: docs/auto-merge-rule.md\n';
ctx += '=== 🔀 ===\n';
process.stdout.write(ctx);
