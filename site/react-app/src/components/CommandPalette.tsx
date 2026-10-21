import React, { useState, useEffect, useRef } from 'react';
import { ScreenMetadata } from '../types/api';

interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
  screens: ScreenMetadata[];
  onSelectScreen: (screen: ScreenMetadata) => void;
}

export const CommandPalette: React.FC<CommandPaletteProps> = ({
  isOpen,
  onClose,
  screens,
  onSelectScreen
}) => {
  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  const filteredScreens = screens.filter(s => {
    const q = query.toLowerCase().trim();
    if (!q) return true;
    return (
      s.title.toLowerCase().includes(q) ||
      s.href.toLowerCase().includes(q) ||
      s.group.toLowerCase().includes(q) ||
      s.stitch_id.toLowerCase().includes(q)
    );
  });

  useEffect(() => {
    if (isOpen) {
      setQuery('');
      setSelectedIndex(0);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [isOpen]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!isOpen) return;

      if (e.key === 'Escape') {
        e.preventDefault();
        onClose();
      } else if (e.key === 'ArrowDown') {
        e.preventDefault();
        setSelectedIndex(prev => (prev + 1) % (filteredScreens.length || 1));
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        setSelectedIndex(prev => (prev - 1 + filteredScreens.length) % (filteredScreens.length || 1));
      } else if (e.key === 'Enter') {
        e.preventDefault();
        if (filteredScreens[selectedIndex]) {
          onSelectScreen(filteredScreens[selectedIndex]);
          onClose();
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, selectedIndex, filteredScreens, onClose, onSelectScreen]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-20 px-4 bg-black/75 backdrop-blur-sm animate-fade-in">
      <div
        className="w-full max-w-2xl bg-[#11131A] border border-[#2D3748] rounded-xl shadow-2xl overflow-hidden flex flex-col max-h-[75vh]"
        onClick={e => e.stopPropagation()}
      >
        {/* Search Input Bar */}
        <div className="flex items-center px-4 py-3 border-b border-[#1E2230] bg-[#161923] gap-3">
          <svg className="w-5 h-5 text-emerald-400 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={e => {
              setQuery(e.target.value);
              setSelectedIndex(0);
            }}
            placeholder="Type screen name, category, or Stitch ID..."
            className="w-full bg-transparent text-sm text-white placeholder-gray-500 focus:outline-none"
          />
          <kbd className="px-2 py-0.5 text-[10px] font-mono bg-[#090A0F] border border-[#2D3748] rounded text-gray-400">
            ESC to close
          </kbd>
        </div>

        {/* Results List */}
        <div className="overflow-y-auto p-2 space-y-1 divide-y divide-transparent">
          {filteredScreens.length === 0 ? (
            <div className="py-8 text-center text-sm text-gray-500 font-mono">
              No matching screens found for &ldquo;{query}&rdquo;
            </div>
          ) : (
            filteredScreens.map((s, index) => {
              const isSelected = index === selectedIndex;
              return (
                <div
                  key={s.href}
                  onClick={() => {
                    onSelectScreen(s);
                    onClose();
                  }}
                  onMouseEnter={() => setSelectedIndex(index)}
                  className={`flex items-center justify-between p-3 rounded-lg cursor-pointer transition-all ${
                    isSelected
                      ? 'bg-emerald-500/15 border border-emerald-500/40 text-white'
                      : 'hover:bg-[#181B26] border border-transparent text-gray-300'
                  }`}
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <span className="w-2 h-2 rounded-full bg-emerald-400 shrink-0"></span>
                    <div className="truncate">
                      <div className="text-sm font-medium truncate">{s.title}</div>
                      <div className="text-xs text-gray-500 font-mono truncate">{s.href}</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 shrink-0 ml-3">
                    <span className="text-[10px] px-2 py-0.5 rounded font-mono bg-[#1E2230] text-gray-400 border border-[#2D3748]">
                      {s.group}
                    </span>
                    <span className="hidden sm:inline text-[9px] px-1.5 py-0.5 rounded font-mono bg-cyan-950/60 text-cyan-400 border border-cyan-800">
                      ID: {s.stitch_id.substring(0, 8)}…
                    </span>
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Footer */}
        <div className="px-4 py-2 border-t border-[#1E2230] bg-[#090A0F] flex items-center justify-between text-[11px] text-gray-500 font-mono">
          <span>Showing {filteredScreens.length} of {screens.length} screens</span>
          <div className="flex items-center gap-3">
            <span>↑↓ Navigate</span>
            <span>↵ Select</span>
          </div>
        </div>
      </div>
    </div>
  );
};
