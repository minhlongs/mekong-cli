/**
 * Status Badge Component - RaaS UX Kit v2.1.79
 * Compact status indicators for robot state communication
 */

import React from 'react';
import { StatusBadgeProps } from '../types/robot';

export const StatusBadge: React.FC<StatusBadgeProps> = ({
  variant,
  size = 'md',
  isPulsing = false,
  isDropdown = false,
  onClick,
  children,
  className = '',
}) => {
  // Size mappings
  const sizeClasses = {
    sm: 'h-5 px-2 text-[11px] gap-1.5',
    md: 'h-6 px-2.5 text-xs gap-2',
    lg: 'h-8 px-3.5 text-sm gap-2.5',
  };

  // Dot size mappings
  const dotSizes = {
    sm: 'w-1.5 h-1.5',
    md: 'w-2 h-2',
    lg: 'w-3 h-3',
  };

  // Variant color mappings using CSS custom properties
  const variantColors = {
    online: {
      dot: 'bg-[var(--color-status-online)]',
      bg: 'bg-[var(--color-status-online-subtle)]',
      text: 'text-[var(--color-text-primary)]',
    },
    offline: {
      dot: 'bg-[var(--color-status-offline)]',
      bg: 'bg-[var(--color-status-offline-subtle)]',
      text: 'text-[var(--color-text-secondary)]',
    },
    charging: {
      dot: 'bg-[var(--color-status-charging)]',
      bg: 'bg-[var(--color-status-charging-subtle)]',
      text: 'text-[var(--color-text-primary)]',
    },
    error: {
      dot: 'bg-[var(--color-status-error)]',
      bg: 'bg-[var(--color-status-error-subtle)]',
      text: 'text-[var(--color-error)]',
    },
    warning: {
      dot: 'bg-[var(--color-status-warning)]',
      bg: 'bg-[var(--color-status-warning-subtle)]',
      text: 'text-[var(--color-caution)]',
    },
    busy: {
      dot: 'bg-[var(--color-status-busy)]',
      bg: 'bg-[var(--color-status-busy-subtle)]',
      text: 'text-[var(--color-text-primary)]',
    },
    idle: {
      dot: 'bg-[var(--color-status-idle)]',
      bg: 'bg-[var(--color-status-idle-subtle)]',
      text: 'text-[var(--color-text-secondary)]',
    },
    paused: {
      dot: 'bg-[var(--color-status-paused)]',
      bg: 'bg-[var(--color-status-paused-subtle)]',
      text: 'text-[var(--color-text-primary)]',
    },
    maintenance: {
      dot: 'bg-[var(--color-status-maintenance)]',
      bg: 'bg-[var(--color-status-maintenance-subtle)]',
      text: 'text-[var(--color-text-primary)]',
    },
  };

  // Statuses that pulse by default (error, warning, charging)
  const shouldPulse =
    isPulsing ||
    variant === 'error' ||
    variant === 'warning' ||
    variant === 'charging';

  const isClickable = onClick !== undefined || isDropdown;

  return (
    <span
      className={`
        inline-flex items-center gap-2
        rounded-full font-medium
        transition-all duration-150
        ${sizeClasses[size]}
        ${variantColors[variant].bg}
        ${variantColors[variant].text}
        ${isClickable ? 'cursor-pointer hover:shadow-sm' : ''}
        ${className}
      `}
      onClick={isClickable ? onClick : undefined}
      role={isClickable ? 'button' : 'status'}
      tabIndex={isClickable ? 0 : undefined}
      aria-label={`Robot status: ${children}`}
    >
      {/* Dot Indicator */}
      <span
        className={`
          rounded-full
          ${dotSizes[size]}
          ${variantColors[variant].dot}
          ${shouldPulse ? 'animate-pulse-badge' : ''}
        `}
        aria-hidden="true"
      />

      {/* Label */}
      <span className="whitespace-nowrap">{children}</span>

      {/* Dropdown Arrow */}
      {isDropdown && (
        <svg
          className="w-3 h-3 opacity-50"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M19 9l-7 7-7-7"
          />
        </svg>
      )}
    </span>
  );
};

export default StatusBadge;
