const fs = require('fs');
const path = require('path');

// Hunter Scanner Prototype
// Scans for: TODO, FIXME, console.log, @ts-ignore
// Generates: Mission file content

const PATTERNS = [
  { name: 'TECH_DEBT', regex: /\/\/\s*(TODO|FIXME):/g, type: 'SIMPLE', pane: 'WORKER' },
  { name: 'CONSOLE_LOG', regex: /console\.(log|warn|error)/g, type: 'SIMPLE', pane: 'WORKER' },
  { name: 'TYPE_SAFETY', regex: /(@ts-ignore|: any)/g, type: 'SIMPLE', pane: 'WORKER' },
  { name: 'SECURITY_RISK', regex: /(password|api_key|secret)\s*=/i, type: 'COMPLEX', pane: 'THINKER' }
];

function scanProject(dir) {
  const issues = [];
  
  function walk(currentDir) {
    const files = fs.readdirSync(currentDir);
    for (const file of files) {
      if (file.startsWith('.') || file === 'node_modules' || file === 'dist' || file === 'build') continue;
      
      const filePath = path.join(currentDir, file);
      const stat = fs.statSync(filePath);
      
      if (stat.isDirectory()) {
        walk(filePath);
      } else if (file.endsWith('.ts') || file.endsWith('.tsx') || file.endsWith('.js')) {
        const content = fs.readFileSync(filePath, 'utf8');
        PATTERNS.forEach(pattern => {
          if (pattern.regex.test(content)) {
            issues.push({
              file: filePath.replace(dir, ''),
              pattern: pattern.name,
              type: pattern.type
            });
          }
        });
      }
    }
  }
  
  walk(dir);
  return issues;
}

// Example usage
const targetDir = process.argv[2] || process.cwd();
console.log(`Hunting in ${targetDir}...`);
const found = scanProject(targetDir);

if (found.length > 0) {
  console.log(`Found ${found.length} issues.`);
  // Group by pattern
  const grouped = found.reduce((acc, issue) => {
    acc[issue.pattern] = (acc[issue.pattern] || 0) + 1;
    return acc;
  }, {});
  console.table(grouped);
  
  // Suggest Mission
  const topIssue = found[0];
  console.log('\n--- Suggested Mission ---');
  console.log(`COMPLEXITY: ${topIssue.type}`);
  console.log(`TIMEOUT: 15`);
  console.log(`PROJECT: ${path.basename(targetDir)}`);
  console.log(`\n/cook "Fix ${topIssue.pattern} issues in ${topIssue.file} and others. Found count: ${grouped[topIssue.pattern]}" --auto`);
} else {
  console.log("Clean code! No prey for the Hunter.");
}
