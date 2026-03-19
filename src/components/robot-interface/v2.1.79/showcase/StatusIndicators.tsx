/**
 * Status Indicators Section - Robot status badges with glow effects
 */

import React from 'react';
import { StatusBadge } from '../../atoms';
import { TokenCard } from './TokenCard';

interface StatusIndicatorsProps {
  onCopy: (name: string, value: string) => void;
  copiedToken: string | null;
}

const statusVariants = [
  { variant: 'online' as const, label: 'Online', description: 'Robot operational' },
  { variant: 'offline' as const, label: 'Offline', description: 'Robot disconnected' },
  { variant: 'charging' as const, label: 'Charging', description: 'Battery charging' },
  { variant: 'error' as const, label: 'Error', description: 'Error state' },
  { variant: 'warning' as const, label: 'Warning', description: 'Warning state' },
  { variant: 'busy' as const, label: 'Busy', description: 'Executing mission' },
  { variant: 'idle' as const, label: 'Idle', description: 'Standing by' },
  { variant: 'paused' as const, label: 'Paused', description: 'Mission paused' },
  { variant: 'maintenance' as const, label: 'Maintenance', description: 'Under maintenance' },
];

const glowTokens = [
  { name: '--glow-online', value: 'var(--glow-online)' },
  { name: '--glow-offline', value: 'var(--glow-offline)' },
  { name: '--glow-charging', value: 'var(--glow-charging)' },
  { name: '--glow-error', value: 'var(--glow-error)' },
  { name: '--glow-warning', value: 'var(--glow-warning)' },
  { name: '--glow-busy', value: 'var(--glow-busy)' },
  { name: '--glow-idle', value: 'var(--glow-idle)' },
];

const statusColors = [
  { name: '--color-status-online', value: 'var(--color-status-online)' },
  { name: '--color-status-offline', value: 'var(--color-status-offline)' },
  { name: '--color-status-charging', value: 'var(--color-status-charging)' },
  { name: '--color-status-error', value: 'var(--color-status-error)' },
  { name: '--color-status-warning', value: 'var(--color-status-warning)' },
  { name: '--color-status-busy', value: 'var(--color-status-busy)' },
  { name: '--color-status-idle', value: 'var(--color-status-idle)' },
  { name: '--color-status-paused', value: 'var(--color-status-paused)' },
  { name: '--color-status-maintenance', value: 'var(--color-status-maintenance)' },
];

export const StatusIndicators: React.FC<StatusIndicatorsProps> = ({ onCopy, copiedToken }) => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-xl)' }}>
      {/* Status Badges */}
      <div>
        <h3 style={subTitleStyle}>Status Badges (All Sizes)</h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-lg)' }}>
          {statusVariants.map((status) => (
            <div key={status.variant} style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-md)', flexWrap: 'wrap' }}>
              <StatusBadge variant={status.variant} size="sm">{status.label}</StatusBadge>
              <StatusBadge variant={status.variant} size="md">{status.label}</StatusBadge>
              <StatusBadge variant={status.variant} size="lg">{status.label}</StatusBadge>
              <span style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-body-sm)' }}>
                {status.description}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Pulsing Badges */}
      <div>
        <h3 style={subTitleStyle}>Pulsing Status Indicators</h3>
        <div style={{ display: 'flex', gap: 'var(--spacing-md)', flexWrap: 'wrap' }}>
          {['error', 'warning', 'charging'].map((variant) => (
            <StatusBadge
              key={variant}
              variant={variant as any}
              size="lg"
              isPulsing
            >
              {variant.charAt(0).toUpperCase() + variant.slice(1)}
            </StatusBadge>
          ))}
        </div>
      </div>

      {/* Glow Effects */}
      <div>
        <h3 style={subTitleStyle}>Status Glow Tokens</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 'var(--spacing-md)' }}>
          {glowTokens.map((token) => (
            <div key={token.name} style={{ backgroundColor: 'var(--color-surface)', padding: 'var(--spacing-md)', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-border)' }}>
              <TokenCard tokenName={token.name} tokenValue={token.value} onCopy={onCopy} />
              <div style={{
                marginTop: 'var(--spacing-md)',
                display: 'flex',
                justifyContent: 'center',
                padding: 'var(--spacing-lg)',
              }}>
                <div style={{
                  width: '48px',
                  height: '48px',
                  borderRadius: 'var(--radius-full)',
                  backgroundColor: token.value.includes('online') ? 'var(--color-status-online)' :
                                  token.value.includes('offline') ? 'var(--color-status-offline)' :
                                  token.value.includes('charging') ? 'var(--color-status-charging)' :
                                  token.value.includes('error') ? 'var(--color-status-error)' :
                                  token.value.includes('warning') ? 'var(--color-status-warning)' :
                                  token.value.includes('busy') ? 'var(--color-status-busy)' :
                                  'var(--color-status-idle)',
                  boxShadow: token.value,
                }} />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Status Color Tokens */}
      <div>
        <h3 style={subTitleStyle}>Status Color Tokens</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 'var(--spacing-md)' }}>
          {statusColors.map((token) => (
            <div key={token.name} style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-sm)', backgroundColor: 'var(--color-surface)', padding: 'var(--spacing-sm)', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-border)' }}>
              <div style={{
                width: '24px',
                height: '24px',
                borderRadius: 'var(--radius-full)',
                backgroundColor: token.value,
                flexShrink: 0,
              }} />
              <TokenCard tokenName={token.name} tokenValue={token.value} compact onCopy={onCopy} />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

const subTitleStyle: React.CSSProperties = {
  fontSize: 'var(--font-size-title)',
  fontWeight: 'var(--font-weight-semibold)',
  color: 'var(--color-text-primary)',
  marginBottom: 'var(--spacing-md)',
};
