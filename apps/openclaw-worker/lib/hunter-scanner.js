const fs = require('fs');
const path = require('path');

// Hunter Scanner Module
// Scans for: TODO, FIXME, console.log, @ts-ignore, secrets
// Generates: Mission content object

const PATTERNS = [
  { name: 'TECH_DEBT', regex: /\/\/\s*(TODO|FIXME):/g, type: 'SIMPLE', pane: 'WORKER', limit: 10 },
  { name: 'CONSOLE_LOG', regex: /console\.(log|warn|error)/g, type: 'SIMPLE', pane: 'WORKER', limit: 20 },
  { name: 'TYPE_SAFETY', regex: /(@ts-ignore|: any)/g, type: 'SIMPLE', pane: 'WORKER', limit: 15 },
  { name: 'SECURITY_RISK', regex: /(password|api_key|secret)\s*=/i, type: 'COMPLEX', pane: 'THINKER', limit: 5 }
];

function scanProject(dir, options = {}) {
  const issues = [];
  const maxIssues = options.maxIssues || 50;
  
  function walk(currentDir) {
    if (issues.length >= maxIssues) return;
    
    let files;
    try {
      files = fs.readdirSync(currentDir);
    } catch (e) { return; }

    for (const file of files) {
      if (issues.length >= maxIssues) return;
      if (file.startsWith('.') || file === 'node_modules' || file === 'dist' || file === 'build' || file === '.next') continue;
      
      const filePath = path.join(currentDir, file);
      let stat;
      try {
        stat = fs.statSync(filePath);
      } catch (e) { continue; }
      
      if (stat.isDirectory()) {
        walk(filePath);
      } else if (file.endsWith('.ts') || file.endsWith('.tsx') || file.endsWith('.js')) {
        const content = fs.readFileSync(filePath, 'utf8');
        PATTERNS.forEach(pattern => {
          if (pattern.regex.test(content)) {
            // Check if we already have enough of this type
            const curTypeCount = issues.filter(i => i.pattern === pattern.name).length;
            if (curTypeCount < (pattern.limit || 10)) {
               issues.push({
                file: filePath.replace(dir, ''),
                pattern: pattern.name,
                type: pattern.type,
                pane: pattern.pane,
                // simple line finding
                line: (content.substring(0, pattern.regex.lastIndex).match(/\n/g) || []).length + 1
              });
            }
          }
        });
      }
    }
  }
  
  walk(dir);
  return issues;
}

// Gemini Flash Verification (The Beggar Strategy)
async function verifyIssueWithGemini(fileContent, pattern, filePath) {
  try {
    const PROXY_URL = 'http://127.0.0.1:8080/v1/chat/completions';
    const MODEL = 'moonshotai/kimi-k2.5'; // Nvidia free tier via Proxy (was gemini-2.5-flash)

    const response = await fetch(PROXY_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: MODEL,
        messages: [
          { role: "system", content: "You are a Senior Code Auditor. Verify if the code snippet contains a REAL issue relating to the pattern. Return JSON: { isReal: boolean, severity: 'low'|'high', fixSuggestion: string }" },
          { role: "user", content: `Pattern: ${pattern}\nFile: ${filePath}\n\nCode snippet:\n${fileContent.slice(0, 2000)}...` }
        ],
        temperature: 0.1
      })
    });

    if (!response.ok) return { isReal: true, note: "Verification skipped (API Error)" }; // Fail safe: assume real
    const data = await response.json();
    
    // Parse JSON from content (handle markdown wrapping)
    let content = data.choices[0].message.content;
    content = content.replace(/```json/g, '').replace(/```/g, '').trim();
    return JSON.parse(content);

  } catch (e) {
    return { isReal: true, note: `Verification skipped: ${e.message}` };
  }
}

async function generateHunterMission(project, projectDir) {
  const issues = scanProject(projectDir);
  
  if (issues.length === 0) return null;
  
  // Pick the most critical or frequent issue type
  const counts = issues.reduce((acc, i) => { acc[i.pattern] = (acc[i.pattern]||0)+1; return acc; }, {});
  
  // Priority: SECURITY > TYPE_SAFETY > TECH_DEBT > CONSOLE_LOG
  let selectedPattern = 'CONSOLE_LOG';
  if (counts['SECURITY_RISK'] > 0) selectedPattern = 'SECURITY_RISK';
  else if (counts['TYPE_SAFETY'] > 0) selectedPattern = 'TYPE_SAFETY';
  else if (counts['TECH_DEBT'] > 0) selectedPattern = 'TECH_DEBT';
  
  const targetIssues = issues.filter(i => i.pattern === selectedPattern);
  const topIssue = targetIssues[0];
  
  // VERIFICATION STEP (The Beggar Strategy)
  // Read file content and verify with Gemini Flash
  try {
    const content = require('fs').readFileSync(path.join(projectDir, topIssue.file), 'utf8');
    const verification = await verifyIssueWithGemini(content, selectedPattern, topIssue.file);
    
    if (!verification.isReal) {
      console.log(`[HUNTER] 🙈 False positive detected in ${topIssue.file} (Gemini Check)`);
      return null;
    }
    console.log(`[HUNTER] 🎯 Target Verified: ${topIssue.file} (${verification.severity})`);
  } catch (e) {
    // If read fails, skip
    console.log(`[HUNTER] Read error: ${e.message}`);
  }

  const targetFile = topIssue.file;
  const targetPane = topIssue.pane;
  const complexity = topIssue.type;
  
  const missionContent = `COMPLEXITY: ${complexity}
TIMEOUT: 20
PROJECT: ${project}

/cook "HUNTER AGENT: ${selectedPattern} cleanup. Trả lời bằng TIẾNG VIỆT.
Found ${targetIssues.length} issues of type ${selectedPattern}.
Target Verified by Gemini Flash: ${targetFile}.
Task:
1. Scan ${targetFile} and fix ${selectedPattern}.
2. Scan other files if possible within timeout.
3. Verify fixes (build/lint).
4. Report: FIXED_COUNT, REMAINING_COUNT." --auto
`;

  return { content: missionContent, pattern: selectedPattern };
}

module.exports = { scanProject, generateHunterMission };

