/**
 * Main dashboard page: Phase 3 implementation with signals, P&L analytics,
 * admin controls, and real-time WebSocket updates.
 */
import { useState, useEffect } from 'react';
import { useTradingStore } from '../stores/trading-store';
import { useWebSocketPriceFeed } from '../hooks/use-websocket-price-feed';
import { useDashboardWebSocket } from '../hooks/use-dashboard-websocket';
import { useSignals } from '../hooks/use-signals';
import { usePnlAnalytics } from '../hooks/use-pnl-analytics';
import { useAdminControls } from '../hooks/use-admin-controls';
import { useHealthStatus } from '../hooks/use-health-status';

// Phase 3 Components
import { StatsRow } from '../components/stats-row';
import { SignalsPanel } from '../components/signals-panel';
import { PnLAnalyticsChart } from '../components/pnl-analytics-chart';
import { AdminControls } from '../components/admin-controls';

// Legacy Components (Phase 1/2)
import { PriceTickerStrip } from '../components/price-ticker-strip';
import { PositionsTableSortable } from '../components/positions-table-sortable';
import { SpreadOpportunitiesCardGrid } from '../components/spread-opportunities-card-grid';
import { EquityCurveChart } from '../components/equity-curve-pnl-chart';
import { CacheStatus } from '../components/cache-status';
import { StrategyStatusPanel } from '../components/strategy-status-panel';
import { TradeHistoryFeed } from '../components/trade-history-feed';

function useNow(): string {
  const [now, setNow] = useState(() => new Date().toLocaleTimeString('en-US', { hour12: false }));
  useEffect(() => {
    const id = setInterval(() => setNow(new Date().toLocaleTimeString('en-US', { hour12: false })), 1000);
    return () => clearInterval(id);
  }, []);
  return now;
}

export function DashboardPage() {
  // Phase 1/2 WebSocket for trading data
  useWebSocketPriceFeed();

  // Phase 3 WebSocket for dashboard updates
  useDashboardWebSocket();

  // Phase 3 API hooks
  const { signals, loading: signalsLoading, error: signalsError, refresh: refreshSignals } = useSignals(0, 50);
  const { metrics, loading: pnlLoading, error: pnlError } = usePnlAnalytics();
  const { status: adminStatus, halt, resume, loading: adminLoading, error: adminError, refresh: refreshAdmin } = useAdminControls();
  useHealthStatus();

  // Trading store data (Phase 1/2)
  const connected = useTradingStore((s: any) => s.connected);
  const positions = useTradingStore((s: any) => s.positions);
  const spreads = useTradingStore((s: any) => s.spreads);
  const strategies = useTradingStore((s: any) => s.strategies);
  const trades = useTradingStore((s: any) => s.trades);
  const botStatus = useTradingStore((s: any) => s.botStatus);

  const lastUpdate = useNow();

  // Derived metrics
  const openCount = positions.filter((p: any) => p.status === 'open').length;

  const activeStrategies = strategies?.filter((s: any) => s.enabled).length ?? 0;

  return (
    <div className="space-y-6 font-mono">
      {/* Top bar */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h2 className="text-white text-lg font-bold tracking-tight">Dashboard</h2>
          <p className="text-muted text-xs mt-0.5">Algo Trader - Phase 3</p>
        </div>
        <div className="flex items-center gap-3">
          <CacheStatus />
          <span className="text-muted text-xs">Updated {lastUpdate}</span>
          <div className={`
            flex items-center gap-1.5 px-3 py-1 rounded-full border text-xs font-semibold
            ${connected
              ? 'border-profit/40 bg-profit/10 text-profit'
              : 'border-loss/40 bg-loss/10 text-loss'
            }
          `}>
            <span className={`w-1.5 h-1.5 rounded-full ${connected ? 'bg-profit animate-pulse' : 'bg-loss'}`} />
            {connected ? 'Live' : 'Offline'}
          </div>
        </div>
      </div>

      {/* Stats Row - Phase 3 */}
      <StatsRow
        totalEquity={metrics?.totalPnl}
        openPositions={openCount}
        todayPnl={metrics?.dailyPnl}
        activeStrategies={activeStrategies}
        metrics={metrics}
      />

      {/* Strategy status - Phase 1/2 */}
      <section>
        <h3 className="text-white text-sm font-semibold mb-2 flex items-center gap-2">
          <span className="w-1 h-4 bg-accent rounded-full inline-block" />
          Strategies
        </h3>
        <StrategyStatusPanel strategies={strategies} botStatus={botStatus} />
      </section>

      {/* Main Grid - Phase 3 Components */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* P&L Analytics */}
        <section>
          <h3 className="text-white text-sm font-semibold mb-2 flex items-center gap-2">
            <span className="w-1 h-4 bg-accent rounded-full inline-block" />
            P&L Analytics
          </h3>
          <PnLAnalyticsChart
            metrics={metrics}
            loading={pnlLoading}
            error={pnlError}
          />
        </section>

        {/* Admin Controls */}
        <section>
          <h3 className="text-white text-sm font-semibold mb-2 flex items-center gap-2">
            <span className="w-1 h-4 bg-accent rounded-full inline-block" />
            Admin Controls
          </h3>
          <AdminControls
            status={adminStatus}
            halt={halt}
            resume={resume}
            loading={adminLoading}
            error={adminError}
            onRefresh={refreshAdmin}
          />
        </section>
      </div>

      {/* Signals Panel - Phase 3 */}
      <section>
        <h3 className="text-white text-sm font-semibold mb-2 flex items-center gap-2">
          <span className="w-1 h-4 bg-profit rounded-full inline-block" />
          Arbitrage Signals
          {signals.length > 0 && (
            <span className="text-[10px] text-muted bg-bg-border px-1.5 py-0.5 rounded">
              {signals.length}
            </span>
          )}
        </h3>
        <SignalsPanel
          signals={signals}
          loading={signalsLoading}
          error={signalsError}
          onRefresh={refreshSignals}
        />
      </section>

      {/* Equity curve - Phase 1/2 */}
      <section>
        <h3 className="text-white text-sm font-semibold mb-2 flex items-center gap-2">
          <span className="w-1 h-4 bg-accent rounded-full inline-block" />
          Equity Curve
        </h3>
        <div className="bg-bg-card border border-bg-border rounded-lg p-3">
          <EquityCurveChart positions={positions} />
        </div>
      </section>

      {/* Price ticker strip - Phase 1/2 */}
      <section>
        <h3 className="text-white text-sm font-semibold mb-2 flex items-center gap-2">
          <span className="w-1 h-4 bg-accent rounded-full inline-block" />
          Live Prices
        </h3>
        <div className="bg-bg-card border border-bg-border rounded-lg overflow-hidden">
          <PriceTickerStrip />
        </div>
      </section>

      {/* Spread opportunities - Phase 1/2 */}
      <section>
        <h3 className="text-white text-sm font-semibold mb-2 flex items-center gap-2">
          <span className="w-1 h-4 bg-profit rounded-full inline-block" />
          Spread Opportunities
          {spreads.length > 0 && (
            <span className="text-[10px] text-muted bg-bg-border px-1.5 py-0.5 rounded">
              {spreads.length}
            </span>
          )}
        </h3>
        <SpreadOpportunitiesCardGrid spreads={spreads} />
      </section>

      {/* Trade history feed - Phase 1/2 */}
      <section>
        <h3 className="text-white text-sm font-semibold mb-2 flex items-center gap-2">
          <span className="w-1 h-4 bg-warning rounded-full inline-block" />
          Trade History
          {trades.length > 0 && (
            <span className="text-[10px] text-muted bg-bg-border px-1.5 py-0.5 rounded">
              {trades.length}
            </span>
          )}
        </h3>
        <div className="bg-bg-card border border-bg-border rounded-lg overflow-hidden">
          <TradeHistoryFeed trades={trades} />
        </div>
      </section>

      {/* Positions table - Phase 1/2 */}
      <section>
        <h3 className="text-white text-sm font-semibold mb-2 flex items-center gap-2">
          <span className="w-1 h-4 bg-muted rounded-full inline-block" />
          Positions
          {positions.length > 0 && (
            <span className="text-[10px] text-muted bg-bg-border px-1.5 py-0.5 rounded">
              {positions.length}
            </span>
          )}
        </h3>
        <div className="bg-bg-card border border-bg-border rounded-lg overflow-hidden">
          <PositionsTableSortable positions={positions} />
        </div>
      </section>
    </div>
  );
}
