import React from 'react';

interface BentoCardProps {
  title?: string;
  subtitle?: string;
  badge?: string;
  badgeColor?: 'emerald' | 'cyan' | 'amber' | 'crimson';
  actionButton?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
  colSpan?: 1 | 2 | 3 | 4;
  glowing?: boolean;
}

export const BentoCard: React.FC<BentoCardProps> = ({
  title,
  subtitle,
  badge,
  badgeColor = 'emerald',
  actionButton,
  children,
  className = '',
  colSpan = 1,
  glowing = false
}) => {
  const colSpanClasses = {
    1: 'col-span-1',
    2: 'col-span-1 md:col-span-2',
    3: 'col-span-1 md:col-span-2 lg:col-span-3',
    4: 'col-span-1 md:col-span-2 lg:col-span-4'
  }[colSpan];

  const badgeStyles = {
    emerald: 'bg-emerald-950/60 text-emerald-400 border-emerald-800',
    cyan: 'bg-cyan-950/60 text-cyan-400 border-cyan-800',
    amber: 'bg-amber-950/60 text-amber-400 border-amber-800',
    crimson: 'bg-red-950/60 text-red-400 border-red-800'
  }[badgeColor];

  return (
    <div
      className={`relative bg-[#11131A] border border-[#1E2230] rounded-xl p-5 transition-all duration-300 hover:border-[#2D3748] hover:shadow-[0_8px_30px_-4px_rgba(0,0,0,0.6)] ${colSpanClasses} ${
        glowing ? 'border-emerald-500/40 shadow-[0_0_20px_rgba(16,185,129,0.15)]' : ''
      } ${className}`}
    >
      {/* Top Header if title or badge present */}
      {(title || badge || actionButton) && (
        <div className="flex items-center justify-between gap-3 mb-4 pb-3 border-b border-[#1E2230]/60">
          <div className="min-w-0">
            {title && (
              <h3 className="text-sm font-bold text-white tracking-wide truncate">
                {title}
              </h3>
            )}
            {subtitle && (
              <p className="text-xs text-gray-400 mt-0.5 truncate">
                {subtitle}
              </p>
            )}
          </div>
          <div className="flex items-center gap-2 shrink-0">
            {badge && (
              <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-mono font-medium border ${badgeStyles}`}>
                {badge}
              </span>
            )}
            {actionButton}
          </div>
        </div>
      )}

      {/* Card Content Body */}
      <div>{children}</div>
    </div>
  );
};
