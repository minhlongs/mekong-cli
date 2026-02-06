// PM2 Ecosystem Configuration for OpenClaw Bridge
// Auto-restart, auto-update tunnel URL, always ON

module.exports = {
  apps: [
    {
      name: 'openclaw-bridge',
      script: 'bridge-server.js',
      cwd: '/Users/macbookprom1/mekong-cli/apps/openclaw-worker',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '200M',
      env: {
        NODE_ENV: 'production',
        PORT: 8765
      }
    },
    {
      name: 'openclaw-tunnel',
      script: 'tunnel-manager.sh',
      cwd: '/Users/macbookprom1/mekong-cli/apps/openclaw-worker',
      interpreter: '/bin/bash',
      instances: 1,
      autorestart: true,
      watch: false,
      restart_delay: 5000,
    }
  ]
};
