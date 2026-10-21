/**
 * RobotStatusPanel Component - RaaS UX Kit v2.1.79
 * Multi-metric health dashboard for real-time robot status monitoring
 */
import React, { useCallback } from 'react';
import { StatusBadge } from '../atoms/StatusBadge';
import { StatCard } from '../molecules/StatCard';
import { Icon } from '../atoms/Icon';
import { Button } from '../atoms/Button';
import { RobotConnectionState, RobotMode, BatteryHealth, SignalQuality, TemperatureState } from '../types/robot';
import { Trend } from '../types/telemetry';

export interface RobotStatusPanelProps {
  robotId: string;
  robotName?: string;
  battery: { level: number; charging: boolean; health: BatteryHealth; estimatedRuntime?: number };
  signal: { strength: number; type: 'wifi' | 'cellular' | 'ethernet'; quality: SignalQuality };
  temperature: { current: number; max: number; state: TemperatureState };
  mode: { current: RobotMode; subMode?: string; activeSince: Date };
  connectionState: RobotConnectionState;
  lastSeen?: Date;
  refreshInterval?: number;
  onExpand?: () => void;
  onQuickAction?: (action: string) => void;
  onEmergencyStop?: () => void;
  className?: string;
  compact?: boolean;
}

const connectionConfig = {
  online: { label: 'Online', variant: 'online' as const, pulsing: false },
  offline: { label: 'Offline', variant: 'offline' as const, pulsing: false },
  reconnecting: { label: 'Reconnecting...', variant: 'warning' as const, pulsing: true },
  unknown: { label: 'Unknown', variant: 'idle' as const, pulsing: false },
};

const modeLabels: Record<RobotMode, string> = {
  auto: 'AUTO', manual: 'MANUAL', teleop: 'TELEOP', charging: 'CHARGING', sleep: 'SLEEP', error: 'ERROR',
};

export const RobotStatusPanel: React.FC<RobotStatusPanelProps> = ({
  robotId,
  robotName,
  battery,
  signal,
  temperature,
  mode,
  connectionState,
  lastSeen,
  onExpand,
  onQuickAction,
  onEmergencyStop,
  className = '',
  compact = false,
}) => {
  const connConfig = connectionConfig[connectionState];

  const formatLastSeen = useCallback((date?: Date) => {
    if (!date) return '';
    const diff = Date.now() - date.getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    if (minutes < 1) return 'Just now';
    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    return date.toLocaleDateString();
  }, []);

  const getSignalTrend = (): Trend => {
    const val = signal.quality === 'excellent' ? 0 : signal.quality === 'good' ? -5 : signal.quality === 'fair' ? -15 : -30;
    return { direction: val >= 0 ? 'up' : 'down', value: Math.abs(val), period: '1h' };
  };

  const getTemperatureTrend = (): Trend => {
    const val = temperature.state === 'cold' ? -10 : temperature.state === 'normal' ? 0 : temperature.state === 'warm' ? 5 : 15;
    return { direction: val >= 0 ? 'up' : 'down', value: Math.abs(val), period: '1h' };
  };

  const handleEmergencyStop = useCallback(() => {
    if (window.confirm('EMERGENCY STOP\n\nThis will immediately halt all robot operations.\n\nAre you sure?')) onEmergencyStop?.();
  }, [onEmergencyStop]);

  return (
    <div
      className={`flex flex-col bg-[var(--color-surface)] border border-[var(--color-border)] rounded-[var(--radius-lg)] p-4 transition-all duration-200 ${compact ? 'gap-3' : 'gap-4'} ${className}`}
      role="region"
      aria-label={`Robot status: ${robotName || robotId}`}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div
            className={`w-10 h-10 rounded-full flex items-center justify-center ${
              connectionState === 'online' ? 'bg-[var(--color-success-subtle)]' : connectionState === 'offline' ? 'bg-[var(--color-error-subtle)]' : 'bg-[var(--color-caution-subtle)]'
            }`}
          >
            <Icon size="lg" color={connectionState === 'online' ? 'success' : connectionState === 'offline' ? 'error' : 'warning'}>
              {connectionState === 'offline' ? <path d="M15 9l-6 6M9 9l6 6" /> : <circle cx="12" cy="12" r="10" />}
            </Icon>
          </div>
          <div>
            <h3 className="text-base font-semibold text-[var(--color-text-primary)]">{robotName || robotId}</h3>
            {lastSeen && connectionState !== 'online' && <p className="text-xs text-[var(--color-text-tertiary)]">Last seen: {formatLastSeen(lastSeen)}</p>}
          </div>
        </div>

        <div className="flex items-center gap-2">
          {onEmergencyStop && (
            <Button
              variant="emergency-stop"
              size="sm"
              onClick={handleEmergencyStop}
              className="min-w-[80px]"
              aria-label="Emergency stop"
              icon={<svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true"><rect x="4" y="4" width="16" height="16" rx="2" /></svg>}
            >
              STOP
            </Button>
          )}
          <StatusBadge variant={connConfig.variant} size="sm" isPulsing={connConfig.pulsing} isDropdown={false}>{connConfig.label}</StatusBadge>
        </div>
      </div>

      <div className={`grid gap-3 ${compact ? 'grid-cols-2' : 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-4'}`}>
        <StatCard type="battery" value={battery.level} label="Battery" unit="%" thresholds={{ min: 0, max: 100, critical: 20 }} variant={compact ? 'compact' : 'default'} />
        <StatCard
          type="signal" value={Math.round(signal.strength)} label="Signal" unit="dBm" trend={getSignalTrend()}
          quality={signal.quality === 'excellent' || signal.quality === 'good' ? 'good' : signal.quality === 'fair' ? 'warning' : 'critical'}
          variant={compact ? 'compact' : 'default'}
        />
        <StatCard
          type="temperature" value={Math.round(temperature.current)} label="Temperature" unit="°C" trend={getTemperatureTrend()}
          thresholds={{ min: 0, max: 100, critical: 80 }}
          quality={temperature.state === 'normal' || temperature.state === 'cold' ? 'good' : temperature.state === 'warm' ? 'warning' : 'critical'}
          variant={compact ? 'compact' : 'default'}
        />
        <div className={`flex flex-col justify-between bg-[var(--color-surface)] border border-[var(--color-border)] rounded-[var(--radius-lg)] ${compact ? 'p-3' : 'p-4'}`} role="region" aria-label="Robot mode">
          <div className="flex items-center justify-between">
            <span className="text-sm text-[var(--color-text-secondary)]">Mode</span>
            <Icon size="sm" color="secondary"><circle cx="12" cy="12" r="3" /></Icon>
          </div>
          <div className="mt-2">
            <span className={`text-[var(--color-text-primary)] ${compact ? 'text-lg font-semibold' : 'text-2xl font-bold'}`}>{modeLabels[mode.current]}</span>
            {mode.subMode && <p className="text-xs text-[var(--color-text-tertiary)] mt-1">{mode.subMode}</p>}
          </div>
          {compact && <div className="mt-2"><StatusBadge variant="online" size="sm">Active</StatusBadge></div>}
        </div>
      </div>

      {!compact && onQuickAction && (
        <div className="flex items-center gap-2 pt-2 border-t border-[var(--color-border)]">
          <Button variant="ghost" size="sm" onClick={() => onQuickAction('reboot')}>Reboot</Button>
          <Button variant="ghost" size="sm" onClick={() => onQuickAction('diagnose')}>Diagnose</Button>
          <Button variant="ghost" size="sm" onClick={() => onQuickAction('locate')}>Locate</Button>
          {onExpand && <Button variant="outline" size="sm" onClick={onExpand} className="ml-auto">Details</Button>}
        </div>
      )}
    </div>
  );
};

export default RobotStatusPanel;
