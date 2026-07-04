import js from '@eslint/js';

export default [
  js.configs.recommended,
  {
    languageOptions: {
      globals: {
        process: 'readonly',
        module: 'readonly',
        require: 'readonly',
        exports: 'readonly',
        __dirname: 'readonly',
        __filename: 'readonly',
        console: 'readonly',
        fetch: 'readonly',
        setTimeout: 'readonly',
        setInterval: 'readonly',
        clearTimeout: 'readonly',
        clearInterval: 'readonly',
        AbortController: 'readonly',
        self: 'readonly',
      }
    }
  },
  {
    ignores: [
      '**/node_modules/**',
      '**/.next/**',
      '**/dist/**',
      '**/out/**',
      '**/.venv/**',
      '**/.venv-seed/**',
      '**/.gemini/**',
      '**/.claude/**',
      '**/.codex/**',
      '**/.agent/**',
      '**/.agents/**',
      'apps/well/n8n_codebase/**',
      'apps/**',
      'packages/**',
    ],
  },
];
