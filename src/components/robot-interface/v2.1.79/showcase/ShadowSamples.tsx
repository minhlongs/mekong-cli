/**
 * Shadow Samples Section - Display elevation levels
 */

import React from 'react';
import { TokenCard } from './TokenCard';

interface ShadowSamplesProps {
  onCopy: (name: string, value: string) => void;
  copiedToken: string | null;
}

const shadows = [
  { name: '--shadow-1', value: 'var(--shadow-1)', label: 'Shadow 1 (Subtle)' },
  { name: '--shadow-2', value: 'var(--shadow-2)', label: 'Shadow 2 (Card)' },
  { name: '--shadow-3', value: 'var(--shadow-3)', label: 'Shadow 3 (Elevated)' },
  { name: '--shadow-4', value: 'var(--shadow-4)', label: 'Shadow 4 (Modal)' },
  { name: '--shadow-5', value: 'var(--shadow-5)', label: 'Shadow 5 (Popover)' },
  { name: '--shadow-inner', value: 'var(--shadow-inner)', label: 'Shadow Inner' },
];

const glowShadows = [
  { name: '--glow-shadow-online', value: 'var(--glow-shadow-online)', label: 'Glow Online' },
  { name: '--glow-shadow-error', value: 'var(--glow-shadow-error)', label: 'Glow Error' },
  { name: '--glow-shadow-warning', value: 'var(--glow-shadow-warning)', label: 'Glow Warning' },
  { name: '--glow-shadow-charging', value: 'var(--glow-shadow-charging)', label: 'Glow Charging' },
];

export const ShadowSamples: React.FC<ShadowSamplesProps> = ({ onCopy, copiedToken }) => {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 'var(--spacing-xl)' }}>
      {/* Elevation Shadows */}
      <div>
        <h3 style={subTitleStyle}>Elevation Shadows</h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-lg)' }}>
          {shadows.map((token) => (
            <div key={token.name}>
              <TokenCard tokenName={token.name} tokenValue={token.value} onCopy={onCopy} />
              <div style={{
                marginTop: 'var(--spacing-md)',
                padding: 'var(--spacing-lg)',
                backgroundColor: 'var(--color-surface)',
                borderRadius: 'var(--radius-lg)',
                boxShadow: token.value,
              }}>
                <p style={{ color: 'var(--color-text-primary)', fontWeight: 'var(--font-weight-medium)' }}>
                  {token.label}
                </p>
                <p style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-body-sm)', marginTop: 'var(--spacing-xs)' }}>
                  Sample card with {token.name}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Glow Shadows */}
      <div>
        <h3 style={subTitleStyle}>Glow Effects</h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-lg)' }}>
          {glowShadows.map((token) => (
            <div key={token.name}>
              <TokenCard tokenName={token.name} tokenValue={token.value} onCopy={onCopy} />
              <div style={{
                marginTop: 'var(--spacing-md)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                padding: 'var(--spacing-xl)',
                backgroundColor: 'var(--color-surface-container)',
                borderRadius: 'var(--radius-lg)',
              }}>
                <div style={{
                  width: '64px',
                  height: '64px',
                  borderRadius: 'var(--radius-full)',
                  boxShadow: token.value,
                }}>
                  <div style={{
                    width: '100%',
                    height: '100%',
                    borderRadius: 'var(--radius-full)',
                    backgroundColor: token.value.includes('online') ? 'var(--color-status-online)' :
                                   token.value.includes('error') ? 'var(--color-status-error)' :
                                   token.value.includes('warning') ? 'var(--color-status-warning)' :
                                   'var(--color-status-charging)',
                  }} />
                </div>
              </div>
              <p style={{ textAlign: 'center', color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-body-sm)', marginTop: 'var(--spacing-sm)' }}>
                {token.label}
              </p>
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
