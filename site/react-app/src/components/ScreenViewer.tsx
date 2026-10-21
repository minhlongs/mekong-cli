import React, { useState } from 'react';
import { ScreenMetadata } from '../types/api';

interface ScreenViewerProps {
  currentScreen: ScreenMetadata;
  screens: ScreenMetadata[];
  onSelectScreen: (screen: ScreenMetadata) => void;
  onOpenInNewTab?: (href: string) => void;
}

export const ScreenViewer: React.FC<ScreenViewerProps> = ({
  currentScreen,
  screens,
  onSelectScreen,
  onOpenInNewTab
}) => {
  const [viewMode, setViewMode] = useState<'desktop' | 'tablet' | 'mobile'>('desktop');
  const [iframeLoaded, setIframeLoaded] = useState<boolean>(false);

  const currentIndex = screens.findIndex(s => s.href === currentScreen.href);
  const prevScreen = currentIndex > 0 ? screens[currentIndex - 1] : screens[screens.length - 1];
  const nextScreen = currentIndex < screens.length - 1 ? screens[currentIndex + 1] : screens[0];

  const widthClasses = {
    desktop: 'w-full',
    tablet: 'max-w-3xl mx-auto',
    mobile: 'max-w-sm mx-auto'
  }[viewMode];

  return (
    <div className="flex flex-col h-full bg-[#11131A] border border-[#1E2230] rounded-xl overflow-hidden shadow-2xl">
      {/* Top Controller Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 px-4 py-3 border-b border-[#1E2230] bg-[#161923]">
        <div className="flex items-center gap-3 min-w-0">
          <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 shrink-0 shadow-[0_0_8px_rgba(16,185,129,0.5)]"></span>
          <div className="truncate">
            <h2 className="text-sm font-bold text-white truncate flex items-center gap-2">
              <span>{currentScreen.title}</span>
              <span className="text-[10px] font-mono text-gray-500 font-normal">({currentScreen.href})</span>
            </h2>
            <div className="flex items-center gap-2 text-[11px] font-mono text-gray-400 mt-0.5">
              <span>Group: <strong className="text-gray-200">{currentScreen.group}</strong></span>
              <span>•</span>
              <span>Stitch ID: <strong className="text-cyan-400">{currentScreen.stitch_id.substring(0, 8)}…</strong></span>
            </div>
          </div>
        </div>

        {/* Viewport & Navigation Tools */}
        <div className="flex items-center gap-2 shrink-0">
          {/* Viewport switchers */}
          <div className="hidden sm:flex items-center bg-[#090A0F] border border-[#1E2230] rounded-lg p-0.5 text-xs">
            <button
              onClick={() => setViewMode('desktop')}
              className={`px-2 py-1 rounded ${viewMode === 'desktop' ? 'bg-[#1E2230] text-white font-medium' : 'text-gray-400 hover:text-white'}`}
              title="Desktop View (100%)"
            >
              Desktop
            </button>
            <button
              onClick={() => setViewMode('tablet')}
              className={`px-2 py-1 rounded ${viewMode === 'tablet' ? 'bg-[#1E2230] text-white font-medium' : 'text-gray-400 hover:text-white'}`}
              title="Tablet View (768px)"
            >
              Tablet
            </button>
            <button
              onClick={() => setViewMode('mobile')}
              className={`px-2 py-1 rounded ${viewMode === 'mobile' ? 'bg-[#1E2230] text-white font-medium' : 'text-gray-400 hover:text-white'}`}
              title="Mobile View (380px)"
            >
              Mobile
            </button>
          </div>

          {/* Prev / Next triggers */}
          <div className="flex items-center gap-1">
            <button
              onClick={() => onSelectScreen(prevScreen)}
              className="p-1.5 rounded-lg bg-[#090A0F] border border-[#1E2230] text-gray-300 hover:text-white hover:border-[#2D3748]"
              title={`Prev: ${prevScreen.title}`}
            >
              ←
            </button>
            <button
              onClick={() => onSelectScreen(nextScreen)}
              className="p-1.5 rounded-lg bg-[#090A0F] border border-[#1E2230] text-gray-300 hover:text-white hover:border-[#2D3748]"
              title={`Next: ${nextScreen.title}`}
            >
              →
            </button>
          </div>

          {/* Open full page */}
          <a
            href={currentScreen.href}
            target="_blank"
            rel="noopener noreferrer"
            onClick={(e) => {
              if (onOpenInNewTab) {
                e.preventDefault();
                onOpenInNewTab(currentScreen.href);
              }
            }}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-500/15 border border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/25 text-xs font-mono font-medium transition-colors"
          >
            <span>Open Screen</span>
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
            </svg>
          </a>
        </div>
      </div>

      {/* Frame Container */}
      <div className="flex-1 bg-[#090A0F] p-2 sm:p-4 overflow-hidden flex flex-col justify-center">
        <div className={`h-[680px] rounded-lg border border-[#1E2230] bg-black overflow-hidden shadow-2xl transition-all duration-300 ${widthClasses} relative`}>
          {!iframeLoaded && (
            <div className="absolute inset-0 flex items-center justify-center bg-[#090A0F] text-gray-500 font-mono text-xs">
              <span className="w-3 h-3 rounded-full border-2 border-emerald-400 border-t-transparent animate-spin mr-2"></span>
              Loading {currentScreen.href}…
            </div>
          )}
          <iframe
            src={currentScreen.href}
            title={currentScreen.title}
            className="w-full h-full border-none"
            onLoad={() => setIframeLoaded(true)}
          />
        </div>
      </div>
    </div>
  );
};
