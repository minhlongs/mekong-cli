#!/usr/bin/env node
const { execSync } = require('child_process');
const path = require('path');

process.env.FORCE_COLOR = '1';

try {
  console.log('Starting Next.js build...');
  const output = execSync(
    `"${process.execPath}" "${path.join(__dirname, 'node_modules', 'next', 'dist', 'bin', 'next')}" build`,
    {
      cwd: __dirname,
      stdio: 'inherit',
      env: { ...process, npm_config_workspace: '' }
    }
  );
  process.exit(0);
} catch (error) {
  console.error('Build failed!');
  process.exit(error.status || 1);
}
