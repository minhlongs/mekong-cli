"use client";

import type { LucideIcon } from "lucide-react";
import clsx from "clsx";

interface NavItemProps {
  icon: LucideIcon;
  label: string;
  active?: boolean;
  onClick?: () => void;
}

/**
 * Single icon nav item for the 48px left sidebar rail.
 * Shows tooltip on hover. Active state: 2px teal left border + teal icon.
 */
export function LeftSidebarNavItem({
  icon: Icon,
  label,
  active = false,
  onClick,
}: NavItemProps) {
  return (
    <div className="relative group">
      <button
        onClick={onClick}
        aria-label={label}
        className={clsx(
          "w-12 h-12 flex items-center justify-center transition-colors duration-150",
          "relative border-l-2",
          active
            ? "border-l-[var(--accent-teal-500)] text-[var(--accent-teal-400)] bg-[var(--surface-hover)]"
            : "border-l-transparent text-[var(--text-muted)] hover:text-[var(--text-secondary)] hover:bg-[var(--surface-hover)]"
        )}
      >
        <Icon size={20} strokeWidth={1.5} />
      </button>

      {/* Tooltip */}
      <div
        className={clsx(
          "absolute left-14 top-1/2 -translate-y-1/2 z-50",
          "px-2 py-1 rounded text-xs whitespace-nowrap pointer-events-none",
          "bg-[var(--bg-tertiary)] text-[var(--text-primary)]",
          "opacity-0 group-hover:opacity-100 transition-opacity duration-150",
          "border border-[var(--border-subtle)]"
        )}
      >
        {label}
      </div>
    </div>
  );
}
