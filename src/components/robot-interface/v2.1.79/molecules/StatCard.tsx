/**
 * StatCard Component - RaaS UX Kit v2.1.79
 * Single metric display for robot telemetry dashboards
 */

import React from 'react';
import { StatCardProps, MetricType, Trend } from '../types/telemetry';
import { Icon } from '../atoms/Icon';
import { StatusBadge } from '../atoms/StatusBadge';

// Icon mappings by metric type
const iconMap: Record<MetricType, React.ReactNode> = {
  battery: (
    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <rect x="3" y="6" width="14" height="12" rx="2" strokeWidth="2" />
      <path d="M21 10v4" strokeWidth="2" />
      <path d="M7 10v4" strokeWidth="2" />
    </svg>
  ),
  signal: (
    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path d="M2 20h.01M7 20v-4M12 20V8M17 20V8M22 20V4" strokeWidth="2" />
    </svg>
  ),
  temperature: (
    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path d="M14 14.76V3.5a2.5 2.5 0 00-5 0v11.26a4.5 4.5 0 105 0z" strokeWidth="2" />
    </svg>
  ),
  uptime: (
    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <circle cx="12" cy="12" r="10" strokeWidth="2" />
      <path d="M12 6v6l4 2" strokeWidth="2" />
    </svg>
  ),
  custom: (
    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <circle cx="12" cy="12" r="10" strokeWidth="2" />
    </svg>
  ),
};

// Quality status mappings
const qualityStatusMap: Record<'good' | 'warning' | 'critical', 'online' | 'warning' | 'error'> = {
  good: 'online',
  warning: 'warning',
  critical: 'error',
};

export const StatCard: React.FC<StatCardProps> = ({
  type = 'custom',
  value,
  label,
  unit,
  trend,
  quality = 'good',
  duration,
  thresholds,
  variant = 'default',
  className = '',
}) => {
  // Determine color based on thresholds and quality
  const getStatusFromThresholds = () => {
    if (!thresholds) return quality;

    if (type === 'battery') {
      if (value >= thresholds.good.min) return 'good';
      if (value >= thresholds.warning.min) return 'warning';
      return 'critical';
    }

    if (type === 'temperature') {
      if (value <= thresholds.good.max) return 'good';
      if (value <= thresholds.warning.max) return 'warning';
      return 'critical';
    }

    return quality;
  };

  const status = getStatusFromThresholds();
  const badgeVariant = qualityStatusMap[status];

  // Size mappings by variant
  const sizeClasses = {
    default: 'p-4 gap-3',
    compact: 'p-3 gap-2',
    minimal: 'p-2 gap-1.5',
  };

  const iconSizes = {
    default: 'w-6 h-6',
    compact: 'w-5 h-5',
    minimal: 'w-4 h-4',
  };

  const valueSizes = {
    default: 'text-2xl font-bold',
    compact: 'text-xl font-semibold',
    minimal: 'text-lg font-medium',
  };

  const labelSizes = {
    default: 'text-sm',
    compact: 'text-xs',
    minimal: 'text-xs',
  };

  // Icon color based on status
  const iconColors = {
    good: 'default' as const,
    warning: 'warning' as const,
    critical: 'error' as const,
  };

  return (
    <div
      className={`
        flex flex-col bg-[var(--color-surface)]
        border border-[var(--color-border)]
        rounded-[var(--radius-lg)]
        transition-all duration-200
        hover:shadow-md
        ${sizeClasses[variant]}
        ${className}
      `}
      role="region"
      aria-label={`${label} stat card`}
    >
      {/* Header with Icon and Label */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Icon
            size={variant === 'default' ? 'md' : variant === 'compact' ? 'sm' : 'xs'}
            color={iconColors[status]}
            className={iconSizes[variant]}
          >
            {iconMap[type]}
          </Icon>
          <span className={`text-[var(--color-text-secondary)] ${labelSizes[variant]}`}>
            {label}
          </span>
        </div>

        {duration && (
          <span className="text-[10px] text-[var(--color-text-tertiary)]">
            {duration}
          </span>
        )}
      </div>

      {/* Value Display */}
      <div className="flex items-end gap-2">
        <span className={`text-[var(--color-text-primary)] ${valueSizes[variant]}`}>
          {typeof value === 'number' ? value.toLocaleString() : value}
          {unit && (
            <span className={`ml-1 text-[var(--color-text-tertiary)] ${
              variant === 'default' ? 'text-base' : 'text-sm'
            }`}>
              {unit}
            </span>
          )}
        </span>

        {/* Trend Indicator */}
        {trend && (
          <TrendIndicator trend={trend} variant={variant} />
        )}
      </div>

      {/* Quality Badge (for default variant) */}
      {variant === 'default' && (
        <div className="mt-1">
          <StatusBadge variant={badgeVariant} size="sm">
            {status === 'good' ? 'Optimal' : status === 'warning' ? 'Warning' : 'Critical'}
          </StatusBadge>
        </div>
      )}
    </div>
  );
};

// Trend Indicator Sub-component
const TrendIndicator: React.FC<{ trend: Trend; variant: 'default' | 'compact' | 'minimal' }> = ({
  trend,
  variant,
}) => {
  const sizes = {
    default: 'w-4 h-4 text-xs',
    compact: 'w-3.5 h-3.5 text-[10px]',
    minimal: 'w-3 h-3 text-[9px]',
  };

  const directionColor = {
    up: trend.value > 0
      ? 'text-[var(--color-success)]'
      : 'text-[var(--color-error)]',
    down: trend.value < 0
      ? 'text-[var(--color-error)]'
      : 'text-[var(--color-success)]',
    stable: 'text-[var(--color-text-tertiary)]',
  };

  const directionIcon = {
    up: (
      <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path d="M5 10l7-7 7 7M12 3v18" strokeWidth="2" />
      </svg>
    ),
    down: (
      <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path d="M19 14l-7 7-7-7M12 21V3" strokeWidth="2" />
      </svg>
    ),
    stable: (
      <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path d="M5 12h14" strokeWidth="2" />
      </svg>
    ),
  };

  return (
    <div
      className={`
        inline-flex items-center gap-1
        ${sizes[variant]}
        ${directionColor[trend.direction]}
      `}
      aria-label={`Trend: ${trend.direction} ${Math.abs(trend.value)}% over ${trend.period}`}
    >
      {directionIcon[trend.direction]}
      <span className="font-medium">
        {trend.direction === 'stable' ? '0' : trend.value > 0 ? `+${trend.value}` : trend.value}%
      </span>
    </div>
  );
};

export default StatCard;
