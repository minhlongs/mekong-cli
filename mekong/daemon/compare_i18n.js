const fs = require('fs');

const en = JSON.parse(fs.readFileSync('../anima119/messages/en.json', 'utf8'));
const vi = JSON.parse(fs.readFileSync('../anima119/messages/vi.json', 'utf8'));

function getKeys(obj, prefix = '') {
  let keys = [];
  for (const key in obj) {
    if (typeof obj[key] === 'object' && obj[key] !== null) {
      keys = keys.concat(getKeys(obj[key], prefix + key + '.'));
    } else {
      keys.push(prefix + key);
    }
  }
  return keys;
}

const enKeys = new Set(getKeys(en));
const viKeys = new Set(getKeys(vi));

const missingInVi = [...enKeys].filter(k => !viKeys.has(k));
const missingInEn = [...viKeys].filter(k => !enKeys.has(k));

console.log('--- Missing in vi.json ---');
if (missingInVi.length === 0) console.log('None');
else missingInVi.forEach(k => console.log(k));

console.log('\n--- Missing in en.json ---');
if (missingInEn.length === 0) console.log('None');
else missingInEn.forEach(k => console.log(k));
