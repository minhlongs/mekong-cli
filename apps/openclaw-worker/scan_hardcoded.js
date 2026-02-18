const fs = require('fs');
const path = require('path');

const scanDirs = [
  '../anima119/src/app',
  '../anima119/src/components'
];

const skipPatterns = [
  /t\(['"`].*?['"`]\)/, // t('key')
  /console\.(log|error|warn|info)/,
  /^\s*$/, // empty
  /^{.*}$/, // variables
  /^\d+$/, // numbers
  /^[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]*$/, // symbols
  /^https?:\/\//, // URLs
  /^<.*>$/, // JSX tags
];

const fileExtensions = ['.tsx', '.ts'];

function scanFile(filePath) {
  const content = fs.readFileSync(filePath, 'utf8');
  const lines = content.split('\n');
  const hardcoded = [];

  lines.forEach((line, index) => {
    // 1. Check for text between tags: >Text<
    // This is a very basic regex and might catch false positives or miss complex cases
    // But it's a good starting point for a static scan
    const jsxTextMatches = line.match(/>([^<>{}]+)</g);
    if (jsxTextMatches) {
      jsxTextMatches.forEach(match => {
        const text = match.slice(1, -1).trim();
        if (isValidText(text)) {
           hardcoded.push({ line: index + 1, text, type: 'JSX Text' });
        }
      });
    }

    // 2. Check for attributes: placeholder="Text", alt="Text", title="Text", label="Text"
    const attrMatches = line.match(/(placeholder|alt|title|label|aria-label)=["']([^"']+)["']/g);
    if (attrMatches) {
      attrMatches.forEach(match => {
        const parts = match.split('=');
        const attr = parts[0];
        const text = parts[1].slice(1, -1).trim(); // remove quotes
        if (isValidText(text)) {
           hardcoded.push({ line: index + 1, text, type: `Attribute (${attr})` });
        }
      });
    }

    // 3. Check for specific text strings that might be hardcoded in conditional rendering
    // e.g. status === 'pending' ? 'Pending' : 'Done'
    // This is harder to detect reliably with regex, so we'll skip for now to avoid noise
  });

  if (hardcoded.length > 0) {
    console.log(`\nFile: ${filePath}`);
    hardcoded.forEach(item => {
      console.log(`  Line ${item.line} [${item.type}]: "${item.text}"`);
    });
  }
}

function isValidText(text) {
  if (!text) return false;
  if (text.length < 2) return false; // Ignore single characters
  if (/^\d+$/.test(text)) return false; // Ignore numbers
  if (/^[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?\s]*$/.test(text)) return false; // Ignore symbols
  if (text.includes('className=')) return false; // Ignore props inside tag text
  if (text.startsWith('http')) return false; // Ignore URLs
  if (text.startsWith('/')) return false; // Ignore paths

  // Ignore common technical strings
  const techTerms = ['utf-8', 'width=device-width', 'viewport', 'icon', 'apple-touch-icon'];
  if (techTerms.includes(text.toLowerCase())) return false;

  return true;
}

function walkDir(dir) {
  const files = fs.readdirSync(dir);
  files.forEach(file => {
    const filePath = path.join(dir, file);
    const stat = fs.statSync(filePath);
    if (stat.isDirectory()) {
      walkDir(filePath);
    } else {
      if (fileExtensions.includes(path.extname(file))) {
        scanFile(filePath);
      }
    }
  });
}

console.log('Scanning for hardcoded strings...');
scanDirs.forEach(dir => {
    if (fs.existsSync(dir)) {
        walkDir(dir);
    } else {
        console.log(`Directory not found: ${dir}`);
    }
});
