/**
 * RobotStatusPanel Component - RaaS UX Kit v2.1.79
 * Multi-metric health dashboard for real-time robot status monitoring
 */

import React, { useEffect, useCallback } from 'react';
import { StatusBadge } from '../../atoms/StatusBadge';
import { StatCard } from '../../molecules/StatCard';
import { Icon } from '../../atoms/Icon';
import { Button } from '../../atoms/Button';
import {
  RobotConnectionState,
  RobotMode,
  BatteryHealth,
  SignalQuality,
  TemperatureState,
} from '../../types/robot';
import { Trend } from '../../types/telemetry';

// ============================================
// Props Interface
// ============================================

export interface RobotStatusPanelProps {
  // Identity
  robotId: string;
  robotName?: string;

  // Metrics
  battery: {
    level: number;        // 0-100
    charging: boolean;
    health: BatteryHealth;
    estimatedRuntime?: number; // minutes
  };

  signal: {
    strength: number;     // -100 to -30 dBm
    type: 'wifi' | 'cellular' | 'ethernet';
    quality: SignalQuality;
  };

  temperature: {
    current: number;      // Celsius
    max: number;
    state: TemperatureState;
  };

  mode: {
    current: RobotMode;
    subMode?: string;
    activeSince: Date;
  };

  // Connection
  connectionState: RobotConnectionState;
  lastSeen?: Date;

  // Behavior
  refreshInterval?: number;  // ms (default: 2000)
  onExpand?: () => void;
  onQuickAction?: (action: string) => void;
  onEmergencyStop?: () => void;

  // Styling
  className?: string;
  compact?: boolean;
}

// ============================================
// Connection State Configurations
// ============================================

const connectionConfig = {
  online: {
    label: 'Online',
    variant: 'online' as const,
    pulsing: false,
  },
  offline: {
    label: 'Offline',
    variant: 'offline' as const,
    pulsing: false,
  },
  reconnecting: {
    label: 'Reconnecting...',
    variant: 'warning' as const,
    pulsing: true,
  },
  unknown: {
    label: 'Unknown',
    variant: 'idle' as const,
    pulsing: false,
  },
};

// ============================================
// Mode Display Labels
// ============================================

const modeLabels: Record<RobotMode, string> = {
  auto: 'AUTO',
  manual: 'MANUAL',
  teleop: 'TELEOP',
  charging: 'CHARGING',
  sleep: 'SLEEP',
  error: 'ERROR',
};

// ============================================
// Main Component
// ============================================

export const RobotStatusPanel: React.FC<RobotStatusPanelProps> = ({
  robotId,
  robotName,
  battery,
  signal,
  temperature,
  mode,
  connectionState,
  lastSeen,
  refreshInterval = 2000,
  onExpand,
  onQuickAction,
  onEmergencyStop,
  className = '',
  compact = false,
}) => {
  // Connection config for current state
  const connConfig = connectionConfig[connectionState];

  // Format last seen time
  const formatLastSeen = useCallback((date?: Date) => {
    if (!date) return '';
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);

    if (minutes < 1) return 'Just now';
    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    return date.toLocaleDateString();
  }, []);

  // Get signal quality trend
  const getSignalTrend = (): Trend | undefined => {
    const trendValue = signal.quality === 'excellent' ? 0 :
                       signal.quality === 'good' ? -5 :
                       signal.quality === 'fair' ? -15 : -30;
    return {
      direction: trendValue >= 0 ? 'up' : 'down',
      value: Math.abs(trendValue),
      period: '1h',
    };
  };

  // Get temperature trend
  const getTemperatureTrend = (): Trend | undefined => {
    const trendValue = temperature.state === 'cold' ? -10 :
                       temperature.state === 'normal' ? 0 :
                       temperature.state === 'warm' ? 5 : 15;
    return {
      direction: trendValue >= 0 ? 'up' : 'down',
      value: Math.abs(trendValue),
      period: '1h',
    };
  };

  // Quick actions handler
  const handleQuickAction = useCallback((action: string) => {
    onQuickAction?.(action);
  }, [onQuickAction]);

  // Emergency stop handler with confirmation
  const handleEmergencyStop = useCallback(() => {
    const confirmed = window.confirm(
      '⚠️ EMERGENCY STOP\n\nThis will immediately halt all robot operations.\n\nAre you sure?'
    );
    if (confirmed) {
      onEmergencyStop?.();
    }
  }, [onEmergencyStop]);

  return (
    <div
      className={`
        flex flex-col
        bg-[var(--color-surface)]
        border border-[var(--color-border)]
        rounded-[var(--radius-lg)]
        p-4
        transition-all duration-200
        ${compact ? 'gap-3' : 'gap-4'}
        ${className}
      `}
      role="region"
      aria-label={`Robot status: ${robotName || robotId}`}
    >
      {/* Header with Robot ID and Connection Status */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          {/* Robot Icon */}
          <div
            className={`
              w-10 h-10 rounded-full flex items-center justify-center
              ${connectionState === 'online' ? 'bg-[var(--color-success-subtle)]' :
                connectionState === 'offline' ? 'bg-[var(--color-error-subtle)]' :
                'bg-[var(--color-caution-subtle)]'}
            `}
          >
            <Icon
              size="lg"
              color={
                connectionState === 'online' ? 'success' :
                connectionState === 'offline' ? 'error' : 'warning'
              }
            >
              {connectionState === 'online' ? (
                <circle cx="12" cy="12" r="10" />
              ) : connectionState === 'offline' ? (
                <path d="M15 9l-6 6M9 9l6 6" />
              ) : (
                <circle cx="12" cy="12" r="10" />
              )}
            </Icon>
          </div>

          {/* Robot Info */}
          <div>
            <h3 className="text-base font-semibold text-[var(--color-text-primary)]">
              {robotName || robotId}
            </h3>
            {lastSeen && connectionState !== 'online' && (
              <p className="text-xs text-[var(--color-text-tertiary)]">
                Last seen: {formatLastSeen(lastSeen)}
              </p>
            )}
          </div>
        </div>

        {/* Connection Status and E-Stop */}
        <div className="flex items-center gap-2">
          {/* Emergency Stop Button */}
          {onEmergencyStop && (
            <Button
              variant="emergency-stop"
              size="sm"
              onClick={handleEmergencyStop}
              className="min-w-[80px]"
              aria-label="Emergency stop"
            >
              🔴 STOP
            </Button>
          )}

          {/* Connection Badge */}
          <StatusBadge
            variant={connConfig.variant}
            size="sm"
            isPulsing={connConfig.pulsing}
            isDropdown={false}
          >
            {connConfig.label}
          </StatusBadge>
        </div>
      </div>

      {/* Metrics Grid */}
      <div
        className={`
          grid gap-3
          ${compact
            ? 'grid-cols-2'
            : 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-4'}
        `}
      >
        {/* Battery */}
        <StatCard
          type="battery"
          value={battery.level}
          label="Battery"
          unit="%"
          thresholds={{
            min: 0,
            max: 100,
            critical: 20,
          }}
          variant={compact ? 'compact' : 'default'}
        />

        {/* Signal */}
        <StatCard
          type="signal"
          value={Math.round(signal.strength)}
          label="Signal"
          unit="dBm"
          trend={getSignalTrend()}
          quality={signal.quality === 'excellent' || signal.quality === 'good' ? 'good' :
                   signal.quality === 'fair' ? 'warning' : 'critical'}
          variant={compact ? 'compact' : 'default'}
        />

        {/* Temperature */}
        <StatCard
          type="temperature"
          value={Math.round(temperature.current)}
          label="Temperature"
          unit="°C"
          trend={getTemperatureTrend()}
          thresholds={{
            min: 0,
            max: 100,
            critical: 80,
          }}
          quality={
            temperature.state === 'normal' || temperature.state === 'cold' ? 'good' :
            temperature.state === 'warm' ? 'warning' : 'critical'
          }
          variant={compact ? 'compact' : 'default'}
        />

        {/* Mode */}
        <div
          className={`
            flex flex-col justify-between
            bg-[var(--color-surface)]
            border border-[var(--color-border)]
            rounded-[var(--radius-lg)]
            ${compact ? 'p-3' : 'p-4'}
          `}
          role="region"
          aria-label="Robot mode"
        >
          <div className="flex items-center justify-between">
            <span className="text-sm text-[var(--color-text-secondary)]">
              Mode
            </span>
            <Icon size="sm" color="secondary">
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                <circle cx="12" cy="12" r="3" />
              </svg>
            </Icon>
          </div>
          <div className="mt-2">
            <span className={`text-[var(--color-text-primary)] ${compact ? 'text-lg font-semibold' : 'text-2xl font-bold'}`}>
              {modeLabels[mode.current]}
            </span>
            {mode.subMode && (
              <p className="text-xs text-[var(--color-text-tertiary)] mt-1">
                {mode.subMode}
              </p>
            )}
          </div>
          {compact && (
            <div className="mt-2">
              <StatusBadge variant="online" size="sm">
                Active
              </StatusBadge>
            </div>
          )}
        </div>
      </div>

      {/* Quick Actions (only in non-compact mode) */}
      {!compact && onQuickAction && (
        <div className="flex items-center gap-2 pt-2 border-t border-[var(--color-border)]">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => handleQuickAction('reboot')}
            icon={
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path d="M4 4v5h.058A5.5 5.5 0 0111.5 4.5c1.592 0 3.035.655 4.09 1.707L17 5v6h6l-1.707 1.41A5.45 5.45 0 0119.5 16c0 3.037-2.463 5.5-5.5 5.5S8.5 19.037 8.5 16h-3c0 4.08 3.92 7.5 8.5 7.5s8.5-3.42 8.5-7.5c0-2.118-.816-4.045-2.148-5.482L22 9h-6V3H10L8.593 4.407A7.46 7.46 0 004 4z" />
              </svg>
            }
          >
            Reboot
          </Button>

          <Button
            variant="ghost"
            size="sm"
            onClick={() => handleQuickAction('diagnose')}
            icon={
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
              </svg>
            }
          >
            Diagnose
          </Button>

          <Button
            variant="ghost"
            size="sm"
            onClick={() => handleQuickAction('locate')}
            icon={
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <circle cx="12" cy="12" r="10" strokeWidth="2" />
                <circle cx="12" cy="12" r="3" fill="currentColor" />
              </svg>
            }
          >
            Locate
          </Button>

          {/* Expand Button */}
          {onExpand && (
            <Button
              variant="outline"
              size="sm"
              onClick={onExpand}
              className="ml-auto"
              icon={
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" strokeWidth="2" />
                </svg>
              }
            >
              Details
            </Button>
          )}
        </div>
      )}
    </div>
  );
};

export default RobotStatusPanel;
