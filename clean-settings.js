const fs = require('fs');

const path = '/Users/macbookprom1/mekong-cli/.claude/settings.json';
const settings = JSON.parse(fs.readFileSync(path, 'utf8'));

if (settings.hooks) {
    for (const hookType of Object.keys(settings.hooks)) {
        const rules = settings.hooks[hookType];
        for (let i = rules.length - 1; i >= 0; i--) {
            const rule = rules[i];
            if (rule.hooks) {
                rule.hooks = rule.hooks.filter(h => !(h.command && h.command.includes('entire hooks')));
                // Remove rule if no hooks left
                if (rule.hooks.length === 0) {
                    rules.splice(i, 1);
                }
            }
        }
        // Remove hookType if no rules left
        if (rules.length === 0) {
            delete settings.hooks[hookType];
        }
    }
}

fs.writeFileSync(path, JSON.stringify(settings, null, 2));
console.log('Cleaned settings.json');
