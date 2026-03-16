// src/polymarket-index.ts
// Entry point for the Polymarket 3-strategy trading bot (spec Section 11)
import { PolymarketBotEngine } from "./polymarket/bot-engine";
import { DashboardBridge } from "./polymarket/dashboard-bridge";

const bot = new PolymarketBotEngine();
const dashboard = new DashboardBridge(bot, parseInt(process.env.WS_DASHBOARD_PORT || "3001"));

async function main() {
  // Safety: require explicit confirmation for LIVE mode
  const dryRun = (process.env.DRY_RUN || 'true') === 'true';
  if (!dryRun && !process.env.CONFIRM_LIVE) {
    console.error('⚠️  LIVE MODE requires CONFIRM_LIVE=1 environment variable.');
    console.error('   Set DRY_RUN=true for paper trading, or CONFIRM_LIVE=1 to proceed.');
    process.exit(1);
  }

  dashboard.start();
  await bot.start();
}

process.on("SIGINT", async () => { await bot.stop(); dashboard.stop(); process.exit(0); });
process.on("SIGTERM", async () => { await bot.stop(); dashboard.stop(); process.exit(0); });
main().catch(e => { console.error("Fatal:", e); process.exit(1); });
