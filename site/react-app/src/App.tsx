import React, { useState, useEffect } from 'react';
import { CyberNavbar } from './components/CyberNavbar';
import { CommandPalette } from './components/CommandPalette';
import { VietQRModal } from './components/VietQRModal';
import { BentoCard } from './components/BentoCard';
import { ScreenViewer } from './components/ScreenViewer';
import {
  fetchScreens,
  fetchPlatformStatus,
  fetchCSuiteQuorum,
  verifyTT78,
  computeMerkleAudit,
  SCREENS_CATALOG
} from './services/api';
import {
  ScreenMetadata,
  PlatformStatus,
  CSuiteQuorumResponse,
  TT78VerifyResponse,
  MerkleAuditResponse
} from './types/api';

export const App: React.FC = () => {
  const [screens, setScreens] = useState<ScreenMetadata[]>(SCREENS_CATALOG);
  const [currentScreen, setCurrentScreen] = useState<ScreenMetadata>(SCREENS_CATALOG[0]);
  const [selectedGroup, setSelectedGroup] = useState<string>('All');
  const [isCommandPaletteOpen, setIsCommandPaletteOpen] = useState<boolean>(false);
  const [isVietQROpen, setIsVietQROpen] = useState<boolean>(false);

  // Live Telemetry States
  const [status, setStatus] = useState<PlatformStatus | null>(null);
  const [quorum, setQuorum] = useState<CSuiteQuorumResponse | null>(null);
  const [invoice, setInvoice] = useState<TT78VerifyResponse | null>(null);
  const [merkle, setMerkle] = useState<MerkleAuditResponse | null>(null);
  const [loadingAudit, setLoadingAudit] = useState<boolean>(false);

  useEffect(() => {
    async function loadInitialData() {
      const [screensData, statusData, quorumData] = await Promise.all([
        fetchScreens(),
        fetchPlatformStatus(),
        fetchCSuiteQuorum()
      ]);
      setScreens(screensData);
      setStatus(statusData);
      setQuorum(quorumData);
    }
    loadInitialData();
  }, []);

  const handleRunAudit = async () => {
    setLoadingAudit(true);
    try {
      const [invRes, merRes] = await Promise.all([
        verifyTT78('INV-2026-009842', '0312345678', '0109876543', 15400000, 10),
        computeMerkleAudit()
      ]);
      setInvoice(invRes);
      setMerkle(merRes);
    } finally {
      setLoadingAudit(false);
    }
  };

  const filteredScreens = selectedGroup === 'All'
    ? screens
    : screens.filter(s => s.group === selectedGroup);

  return (
    <div className="min-h-screen bg-[#090A0F] text-gray-100 flex flex-col font-sans selection:bg-emerald-500/30 selection:text-emerald-300">
      <div role="note" className="px-4 py-2 text-center text-xs text-amber-100 bg-amber-950 border-b border-amber-700">
        Interactive demo only. Data is synthetic; no payment, verification, account balance, or ledger is changed.
      </div>
      {/* Global Cyber Navigation */}
      <CyberNavbar
        onOpenCommandPalette={() => setIsCommandPaletteOpen(true)}
        onOpenVietQR={() => setIsVietQROpen(true)}
        activeGroup={selectedGroup}
        onSelectGroup={setSelectedGroup}
        totalScreens={screens.length}
      />

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8 space-y-8">
        {/* Hero Section */}
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 pb-6 border-b border-[#1E2230]">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="px-2 py-0.5 rounded text-[11px] font-mono font-medium bg-emerald-950/60 text-emerald-400 border border-emerald-800">
                INTERACTIVE DEMO
              </span>
              <span className="text-gray-500 text-xs font-mono">•</span>
              <span className="text-gray-400 text-xs font-mono">20 synthetic screens</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
              Mekong Cyber-Bento Horizon
            </h1>
            <p className="text-sm text-gray-400 mt-1 max-w-2xl">
              Product preview with payment-flow, invoice, audit, and executive-consensus simulations. These examples do not perform live verification or modify accounts.
            </p>
          </div>

          <div className="flex items-center gap-2.5">
            <button
              onClick={handleRunAudit}
              disabled={loadingAudit}
              className="flex items-center gap-2 px-4 py-2 rounded-lg bg-[#11131A] border border-cyan-500/40 hover:border-cyan-400 text-cyan-400 text-xs font-mono font-semibold transition-all shadow-[0_0_12px_rgba(6,182,212,0.15)]"
            >
              <span>{loadingAudit ? 'Running demo…' : 'Run demo audit'}</span>
              <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping"></span>
            </button>
          </div>
        </div>

        {/* Bento Telemetry Grid */}
        <section className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Card 1: System Telemetry */}
          <BentoCard
            title="Demo Runtime"
            subtitle="Synthetic preview · no live health check"
            badge="DEMO"
            badgeColor="amber"
          >
            <div className="space-y-2 text-xs font-mono">
              <div className="flex justify-between">
                <span className="text-gray-400">Mode:</span>
                <span className="text-emerald-400 font-bold">{status?.mode || 'synthetic_demo'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Total Screens:</span>
                <span className="text-white font-bold">{screens.length} / 20 Complete</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Swarm Sync:</span>
                <span className="text-cyan-400 font-bold">{status?.swarm_sync || 'NOT_CONNECTED'}</span>
              </div>
            </div>
          </BentoCard>

          {/* Card 2: C-Suite Quorum */}
          <BentoCard
            title="Approval Demo"
            subtitle="Synthetic sample · no votes recorded"
            badge="DEMO · NO VOTES"
            badgeColor="cyan"
          >
            <div className="space-y-2 text-xs font-mono">
              <div className="flex justify-between">
                <span className="text-gray-400">Approvals:</span>
                <span className="text-white font-bold">{quorum?.total_votes ?? 0} of 5 (synthetic)</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Signoff Hash:</span>
                <span className="text-cyan-400 truncate max-w-[130px]">No approval hash</span>
              </div>
              <div className="text-[10px] text-gray-500 truncate" title={quorum?.resolution}>
                {quorum?.resolution || 'Scale Autonomous C-Suite'}
              </div>
            </div>
          </BentoCard>

          {/* Card 3: TT78 Tax Verifier */}
          <BentoCard
            title="Invoice Hash Demo"
            subtitle="Hash calculation only · no verification"
            badge={invoice ? 'DEMO HASH' : 'DEMO ONLY'}
            badgeColor={invoice ? 'emerald' : 'amber'}
          >
            <div className="space-y-2 text-xs font-mono">
              <div className="flex justify-between">
                <span className="text-gray-400">Invoice:</span>
                <span className="text-white font-bold">{invoice?.invoice_id || 'INV-2026-009842'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Stamp:</span>
                <span className="text-emerald-400 truncate max-w-[130px]">
                  {invoice?.digital_stamp || 'No verification performed'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Total VND:</span>
                <span className="text-gray-200">16,940,000 đ</span>
              </div>
            </div>
          </BentoCard>

          {/* Card 4: Merkle Proof */}
          <BentoCard
            title="Merkle Hash Demo"
            subtitle="Synthetic records · no authenticity proof"
            badge={merkle ? 'HASH CALCULATED' : 'DEMO ONLY'}
            badgeColor={merkle ? 'emerald' : 'cyan'}
          >
            <div className="space-y-2 text-xs font-mono">
              <div className="flex justify-between">
                <span className="text-gray-400">Leaves:</span>
                <span className="text-white font-bold">{merkle?.leaf_count || 4} Audit Blocks</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Merkle Root:</span>
                <span className="text-emerald-400 truncate max-w-[130px]" title={merkle?.merkle_root}>
                  {merkle?.merkle_root ? merkle.merkle_root.substring(0, 14) + '…' : 'Uncalculated'}
                </span>
              </div>
              <div className="text-[10px] text-gray-500">
                Standard: NIST FIPS 180-4
              </div>
            </div>
          </BentoCard>
        </section>

        {/* Screen Catalog & Live Viewer Section */}
        <section className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <span>Interactive Screen Inspector</span>
              <span className="text-xs font-mono text-gray-500 font-normal">
                ({filteredScreens.length} screens in category &ldquo;{selectedGroup}&rdquo;)
              </span>
            </h2>
          </div>

          <ScreenViewer
            currentScreen={currentScreen}
            screens={screens}
            onSelectScreen={setCurrentScreen}
          />
        </section>
      </main>

      {/* Modals */}
      <CommandPalette
        isOpen={isCommandPaletteOpen}
        onClose={() => setIsCommandPaletteOpen(false)}
        screens={screens}
        onSelectScreen={setCurrentScreen}
      />

      <VietQRModal
        isOpen={isVietQROpen}
        onClose={() => setIsVietQROpen(false)}
      />
    </div>
  );
};
