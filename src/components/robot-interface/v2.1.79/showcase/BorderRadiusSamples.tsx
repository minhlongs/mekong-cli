/**
 * Border Radius Samples Section
 */

import React from 'react';
import { TokenCard } from './TokenCard';

interface BorderRadiusSamplesProps {
  onCopy: (name: string, value: string) => void;
  copiedToken: string | null;
}

const radiusTokens = [
  { name: '--radius-none', value: 'var(--radius-none)', label: 'None' },
  { name: '--radius-sm', value: 'var(--radius-sm)', label: 'Small (4px)' },
  { name: '--radius-md', value: 'var(--radius-md)', label: 'Medium (8px)' },
  { name: '--radius-lg', value: 'var(--radius-lg)', label: 'Large (12px)' },
  { name: '--radius-xl', value: 'var(--radius-xl)', label: 'XL (16px)' },
  { name: '--radius-2xl', value: 'var(--radius-2xl)', label: '2XL (24px)' },
  { name: '--radius-full', value: 'var(--radius-full)', label: 'Full (Circle)' },
];

const componentRadius = [
  { name: '--radius-button', value: 'var(--radius-button)', label: 'Button' },
  { name: '--radius-button-pill', value: 'var(--radius-button-pill)', label: 'Button Pill' },
  { name: '--radius-input', value: 'var(--radius-input)', label: 'Input' },
  { name: '--radius-card', value: 'var(--radius-card)', label: 'Card' },
  { name: '--radius-modal', value: 'var(--radius-modal)', label: 'Modal' },
  { name: '--radius-chip', value: 'var(--radius-chip)', label: 'Chip' },
  { name: '--radius-badge', value: 'var(--radius-badge)', label: 'Badge' },
  { name: '--radius-avatar', value: 'var(--radius-avatar)', label: 'Avatar' },
  { name: '--radius-toggle', value: 'var(--radius-toggle)', label: 'Toggle' },
  { name: '--radius-panel', value: 'var(--radius-panel)', label: 'Panel' },
];

export const BorderRadiusSamples: React.FC<BorderRadiusSamplesProps> = ({ onCopy, copiedToken }) => {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 'var(--spacing-xl)' }}>
      {/* Base Radius */}
      <div>
        <h3 style={subTitleStyle}>Base Radius Scale</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', gap: 'var(--spacing-md)' }}>
          {radiusTokens.map((token) => (
            <div key={token.name} style={{ textAlign: 'center' }}>
              <TokenCard tokenName={token.name} tokenValue={token.value} compact onCopy={onCopy} />
              <div style={{
                height: '80px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                marginTop: 'var(--spacing-sm)',
              }}>
                <div style={{
                  width: '60px',
                  height: '60px',
                  backgroundColor: 'var(--color-primary)',
                  borderRadius: token.value,
                  transition: 'all var(--transition-normal)',
                }} />
              </div>
              <p style={{ fontSize: 'var(--font-size-body-sm)', color: 'var(--color-text-tertiary)', marginTop: 'var(--spacing-xs)' }}>
                {token.label}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* Component Radius */}
      <div>
        <h3 style={subTitleStyle}>Component Radius</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: 'var(--spacing-md)' }}>
          {componentRadius.map((token) => (
            <div key={token.name} style={{ textAlign: 'center' }}>
              <TokenCard tokenName={token.name} tokenValue={token.value} compact onCopy={onCopy} />
              <div style={{
                height: '60px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                marginTop: 'var(--spacing-sm)',
              }}>
                {token.name.includes('avatar') || token.name.includes('badge') || token.name.includes('chip') || token.name.includes('toggle') ? (
                  <div style={{
                    width: token.name.includes('avatar') ? '48px' : 'auto',
                    minWidth: '60px',
                    height: '32px',
                    backgroundColor: 'var(--color-secondary)',
                    borderRadius: token.value,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: 'var(--color-text-inverse)',
                    fontSize: 'var(--font-size-body-sm)',
                  }}>
                    {token.label}
                  </div>
                ) : (
                  <div style={{
                    width: '60px',
                    height: '32px',
                    backgroundColor: 'var(--color-accent)',
                    borderRadius: token.value,
                  }} />
                )}
              </div>
              <p style={{ fontSize: 'var(--font-size-body-sm)', color: 'var(--color-text-tertiary)', marginTop: 'var(--spacing-xs)' }}>
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
