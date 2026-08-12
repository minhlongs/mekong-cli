#!/usr/bin/env node
/**
 * plugin-init.cjs — Generate a new Mekong CLI plugin skeleton
 *
 * Usage: node scripts/plugin-init.cjs <plugin-name>
 *
 * Creates: plugins/<plugin-name>/
 *   .plugin.json — plugin manifest
 *   SKILL.md     — skill definition (if type includes "skill")
 *   command.md   — command definition (if type includes "command")
 *   index.js     — entry point
 *
 * Prompting: collects all stdin lines into a buffer, printing prompts to stderr.
 * Works for both interactive terminals and piped stdin.
 */
'use strict';

var fs   = require('node:fs');
var path = require('node:path');
var readline = require('node:readline');

// ---- Prompt engine: reads lines from stdin buffer instead of rl.question -------

var _inputBuffer = [];
var _inputDone   = false;
var _waitingResolve = null;

var _rl = readline.createInterface({ input: process.stdin, terminal: false });
_rl.on('line', function (line) {
  if (_waitingResolve) {
    var r = _waitingResolve;
    _waitingResolve = null;
    r(line.trim());
  } else {
    _inputBuffer.push(line.trim());
  }
});
_rl.on('close', function () {
  _inputDone = true;
  if (_waitingResolve) {
    var r = _waitingResolve;
    _waitingResolve = null;
    r('');
  }
});

function prompt(query) {
  process.stderr.write(query);
  return new Promise(function (resolve) {
    if (_inputBuffer.length > 0) {
      resolve(_inputBuffer.shift());
    } else if (_inputDone) {
      resolve('');
    } else {
      _waitingResolve = resolve;
    }
  });
}

// ---- Helper functions ---------------------------------------------------------

function kebabToTitle(str) {
  return str
    .split(/[-_]/)
    .map(function (w) { return w.charAt(0).toUpperCase() + w.slice(1); })
    .join(' ');
}

function kebabToCamel(str) {
  return str
    .split(/[-_]/)
    .map(function (w, i) { return i === 0 ? w : w.charAt(0).toUpperCase() + w.slice(1); })
    .join('');
}

var HOOK_OPTIONS = [
  'SessionStart',
  'UserPromptSubmit',
  'UserPromptComplete',
  'ToolCall',
  'ToolResult',
];

// ---- Templates ----------------------------------------------------------------

function manifestTemplate(params) {
  var obj = {
    name: params.name,
    version: '0.1.0',
    type: params.type,
    description: params.description,
    entry: params.entry,
    requires: [],
    license: 'MIT',
  };
  if (params.hooks.length > 0) {
    obj.hooks = params.hooks;
  }
  return JSON.stringify(obj, null, 2) + '\n';
}

function skillMdTemplate(params) {
  var name  = params.name;
  var title = params.title;
  return [
    '# ' + title,
    '',
    title + ' is a Mekong CLI skill plugin that ' + name + '.',
    '',
    '## Usage',
    '',
    '```',
    'mekong ' + name + ' <args>',
    '```',
    '',
    '## Description',
    '',
    '<!-- Replace with a concise description of what this skill does. -->',
    '',
    '## Arguments',
    '',
    '| Argument | Type | Required | Description |',
    '|----------|------|----------|-------------|',
    '| `--help` | flag | no | Show help |',
    '',
    '## Examples',
    '',
    '```',
    'mekong ' + name + ' --help',
    '```',
    '',
    '## Hooks',
    '',
    '<!-- List hooks this plugin registers and what they do. -->',
    '',
    '## See Also',
    '',
    '- [Plugin manifest](./.plugin.json)',
    '- [Commands](./command.md)',
    '',
  ].join('\n');
}

function commandMdTemplate(params) {
  var name  = params.name;
  var title = params.title;
  return [
    '# ' + title + ' -- `' + name + '`',
    '',
    '## Usage',
    '',
    '```',
    'mekong ' + name + ' [options]',
    '```',
    '',
    '## Description',
    '',
    '<!-- Replace with a concise description of what this command does. -->',
    '',
    '## Options',
    '',
    '| Option | Type | Required | Description |',
    '|--------|------|----------|-------------|',
    '| `--help` | flag | no | Show help |',
    '',
    '## Examples',
    '',
    '```bash',
    'mekong ' + name,
    '```',
    '',
  ].join('\n');
}

function indexJsTemplate(params) {
  var name      = params.name;
  var camelName = params.camelName;
  var hooks     = params.hooks || [];

  // Use String.fromCharCode(96) for backtick chars so the generated
  // index.js source contains valid template-literal expressions.
  var BT = String.fromCharCode(96);

  var hookRegLines = [];
  hooks.forEach(function (h) {
    var fnName  = 'on' + h;
    var comment = {
      SessionStart:       '// Runs when a new session starts -- good for initialising state',
      UserPromptSubmit:   '// Runs after the user submits a prompt -- good for transforming input',
      UserPromptComplete: '// Runs after the assistant finishes responding',
      ToolCall:           '// Runs before a tool is invoked',
      ToolResult:         '// Runs after a tool returns a result',
    }[h] || '// Hook: ' + h;

    hookRegLines.push(
      '  /** @type {import(\'../../types\').HookHandler} */',
      '  ' + fnName + '(payload) {',
      '    ' + comment,
      '    // TODO: implement ' + fnName,
      '    // return payload;',
      '  },',
      ''
    );
  });

  var runLines = [
    '    const [command, ...rest] = args;',
    '',
    '    if (command === \'--help\' || command === \'-h\') {',
    '      console.log(' + BT + 'Usage: mekong ' + name + ' [options]',
    '',
    'Options:',
    '  --help, -h  Show this help',
    '',
    'Description:',
    '  <!-- TODO: describe what ' + name + ' does -->',
    BT + ');',
    '      return 0;',
    '    }',
    '',
    '    console.log(' + BT + name + ': hello from plugin -- args: ${args.join(\' \')}' + BT + ');',
    '    return 0;',
  ];

  return [
    '\'use strict\';',
    '',
    '/**',
    ' * ' + name + ' -- Mekong CLI plugin (' + camelName + ')',
    ' *',
    ' * Source: plugins/' + name + '/',
    ' * Manifest: plugins/' + name + '/.plugin.json',
    ' */',
    '',
    '// ---- Plugin definition ---------------------------------------------------',
    '',
    '/** @type {import(\'../../types\').PluginDefinition} */',
    'const plugin = {',
    '  name: \'' + name + '\',',
    '  hooks: {',
    hookRegLines.join('\n'),
    '  },',
    '',
    '  // ---- Methods called by the CLI -----------------------------------------',
    '',
    '  /**',
    '   * Run the plugin command (triggered via `mekong ' + name + ' <args>`).',
    '   * @param {string[]} args',
    '   * @returns {Promise<number>} exit code',
    '   */',
    '  async run(args) {',
    runLines.join('\n'),
    '  },',
    '};',
    '',
    'module.exports = plugin;',
    '',
  ].join('\n');
}

// ---- Main --------------------------------------------------------------------

async function main() {
  // 1. Plugin name -- from arg or prompt
  var name = process.argv[2];
  if (!name) {
    name = await prompt('Plugin name (kebab-case): ');
    if (!name) {
      console.error('Error: plugin name is required.');
      process.exit(1);
    }
  }

  var PLUGINS_DIR = path.resolve(__dirname, '..', 'plugins');
  var TARGET      = path.join(PLUGINS_DIR, name);

  if (fs.existsSync(TARGET)) {
    console.error('Error: plugins/' + name + '/ already exists.');
    process.exit(1);
  }

  // 2. Type
  var typeRaw = await prompt('Type [skill] (skill / command / both): ');
  var type = (typeRaw || 'skill').toLowerCase();
  if (['skill', 'command', 'both'].indexOf(type) === -1) {
    console.error('Error: type must be "skill", "command", or "both".');
    process.exit(1);
  }

  // 3. Description
  var descDefault = kebabToTitle(name) + ' plugin';
  var description = await prompt('Description (one line): [' + descDefault + '] ');
  if (!description) description = descDefault;

  // 4. Hooks (comma-separated, press Enter for none)
  var hookAnswer = await prompt(
    'Hooks [' + HOOK_OPTIONS.join(', ') + ']\n  (comma-separated, or Enter for none): '
  );
  var hooks = hookAnswer
    ? hookAnswer.split(',').map(function (s) { return s.trim(); }).filter(Boolean)
    : [];

  // Validate hook names
  for (var i = 0; i < hooks.length; i++) {
    if (HOOK_OPTIONS.indexOf(hooks[i]) === -1) {
      console.error('Warning: "' + hooks[i] + '" is not a recognised hook name.');
    }
  }

  // 5. Derived values
  var title     = kebabToTitle(name);
  var camelName = kebabToCamel(name);
  var entry     = 'index.js';

  // ---- Create directory structure ---------------------------------------------

  fs.mkdirSync(TARGET, { recursive: true });

  // .plugin.json
  fs.writeFileSync(
    path.join(TARGET, '.plugin.json'),
    manifestTemplate({ name: name, type: type, description: description, hooks: hooks, entry: entry }),
    'utf-8',
  );

  // SKILL.md
  if (type === 'skill' || type === 'both') {
    fs.writeFileSync(
      path.join(TARGET, 'SKILL.md'),
      skillMdTemplate({ name: name, title: title }),
      'utf-8',
    );
  }

  // command.md
  if (type === 'command' || type === 'both') {
    fs.writeFileSync(
      path.join(TARGET, 'command.md'),
      commandMdTemplate({ name: name, title: title }),
      'utf-8',
    );
  }

  // index.js
  fs.writeFileSync(
    path.join(TARGET, entry),
    indexJsTemplate({ name: name, camelName: camelName, hooks: hooks }),
    'utf-8',
  );

  // ---- Summary ----------------------------------------------------------------

  var indent = '  ';
  console.log('\nPlugin "' + name + '" created at plugins/' + name + '/\n');

  var files = ['.plugin.json'];
  if (type === 'skill' || type === 'both') files.push('SKILL.md');
  if (type === 'command' || type === 'both') files.push('command.md');
  files.push(entry);

  files.forEach(function (f) {
    console.log(indent + 'plugins/' + name + '/' + f);
  });

  console.log('\n' + indent + 'type:        ' + type);
  console.log(indent + 'description: ' + description);
  if (hooks.length > 0) {
    console.log(indent + 'hooks:       ' + hooks.join(', '));
  }
  console.log('\nEdit the placeholder files to implement your plugin.');
}

main().catch(function (err) {
  console.error(err);
  process.exit(1);
});
