/**
 * PM2 Ecosystem — Mekong CLI Social Daemon
 *
 * Runs the social auto-poster + LLM reply bot on M1 Max.
 *
 * Usage:
 *   pm2 start ecosystem.social.cjs        # start daemon
 *   pm2 stop social-daemon                # stop
 *   pm2 logs social-daemon                # view logs
 *   pm2 save && pm2 startup               # persist across reboots
 */

module.exports = {
  apps: [
    {
      name: "social-daemon",
      script: "scripts/social-daemon.sh",
      interpreter: "/bin/bash",
      args: "--interval 60",
      cwd: process.env.HOME + "/mekong-cli",

      // Restart policy
      autorestart: true,
      restart_delay: 30000,     // 30s before restart on crash
      max_restarts: 10,
      min_uptime: "30s",

      // Logging
      log_date_format: "YYYY-MM-DD HH:mm:ss",
      out_file: process.env.HOME + "/.mekong/logs/social-daemon.out.log",
      error_file: process.env.HOME + "/.mekong/logs/social-daemon.err.log",
      merge_logs: false,

      // Environment
      env: {
        NODE_ENV: "production",
        PYTHONUNBUFFERED: "1",
      },
    },
  ],
};
