import React from 'react';

interface CyberNavbarProps {
  onOpenCommandPalette: () => void;
  onOpenVietQR: () => void;
  activeGroup?: string;
  onSelectGroup?: (group: string) => void;
  totalScreens?: number;
}

export const CyberNavbar: React.FC<CyberNavbarProps> = ({
  onOpenCommandPalette,
  onOpenVietQR,
  activeGroup = 'All',
  onSelectGroup,
  totalScreens = 20
}) => {
  const groups = ['All', 'Core', 'Operations', 'Compliance', 'Recipes', 'Integrations', 'Developer', 'Executive'];

  return (
    <header className="sticky top-0 z-40 w-full border-b border-[#1E2230] bg-[#11131A]/85 backdrop-blur-md px-4 lg:px-6 py-2.5 transition-colors">
      <div className="max-w-7xl mx-auto flex items-center justify-between gap-4">
        {/* Brand & Badge */}
        <div className="flex items-center gap-3">
          <a href="index.html" className="flex items-center gap-2 group">
            <div className="w-8 h-8 rounded-lg bg-emerald-500/10 border border-emerald-500/40 flex items-center justify-center text-emerald-400 font-bold group-hover:border-emerald-400 group-hover:shadow-[0_0_12px_rgba(16,185,129,0.3)] transition-all">
              <span className="font-mono text-sm tracking-tighter">MK</span>
            </div>
            <div className="flex flex-col">
              <span className="font-bold text-sm tracking-wider text-white group-hover:text-emerald-400 transition-colors">
                MEKONG CLI
              </span>
              <span className="text-[10px] font-mono text-emerald-400/80 -mt-0.5">
                CYBER-BENTO HORIZON
              </span>
            </div>
          </a>
          <span className="hidden sm:inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-mono font-medium bg-emerald-950/60 border border-emerald-800 text-emerald-400">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
            6.0 PRO ({totalScreens} SCREENS)
          </span>
        </div>

        {/* Group Selector Pills */}
        {onSelectGroup && (
          <div className="hidden md:flex items-center gap-1 overflow-x-auto py-1">
            {groups.map(g => (
              <button
                key={g}
                onClick={() => onSelectGroup(g)}
                className={`px-2.5 py-1 text-xs rounded-lg font-medium transition-all ${
                  activeGroup === g
                    ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 shadow-[0_0_10px_rgba(16,185,129,0.15)]'
                    : 'text-gray-400 hover:text-white hover:bg-[#181B26] border border-transparent'
                }`}
              >
                {g}
              </button>
            ))}
          </div>
        )}

        {/* Actions & Triggers */}
        <div className="flex items-center gap-2.5">
          {/* React SPA Link */}
          <a
            href="/app/"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-cyan-950/60 border border-cyan-800 text-cyan-400 hover:bg-cyan-900/60 hover:text-cyan-300 transition-all text-xs font-mono font-medium shadow-[0_0_10px_rgba(6,182,212,0.15)]"
            title="Open React SPA Dashboard"
          >
            <span className="w-1.5 h-1.5 rounded-full bg-cyan-400"></span>
            <span>React App</span>
          </a>

          {/* Cmd+K Search Trigger */}
          <button
            onClick={onOpenCommandPalette}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[#090A0F] border border-[#1E2230] text-gray-400 hover:text-white hover:border-[#2D3748] transition-all text-xs group"
            title="Search screens (Cmd+K)"
          >
            <svg className="w-3.5 h-3.5 text-gray-400 group-hover:text-emerald-400 transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <span className="hidden sm:inline">Search Screens...</span>
            <kbd className="hidden sm:inline-block px-1.5 py-0.5 text-[10px] font-mono bg-[#181B26] border border-[#2D3748] rounded text-gray-400">⌘K</kbd>
          </button>

          {/* VietQR Top-up CTA */}
          <button
            onClick={onOpenVietQR}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-medium text-xs shadow-[0_0_15px_rgba(16,185,129,0.25)] hover:shadow-[0_0_20px_rgba(16,185,129,0.4)] transition-all"
          >
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4v16m8-8H4" />
            </svg>
            <span>VietQR Pay</span>
          </button>
        </div>
      </div>
    </header>
  );
};
