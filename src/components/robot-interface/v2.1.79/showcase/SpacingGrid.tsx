/**
 * Spacing Grid Section - Visualize 8pt grid system
 */

import React from 'react';
import { TokenCard } from './TokenCard';

interface SpacingGridProps {
  onCopy: (name: string, value: string) => void;
  copiedToken: string | null;
}

const spacingTokens = [
  { name: '--spacing-none', value: 'var(--spacing-none)', pixels: 0 },
  { name: '--spacing-xs', value: 'var(--spacing-xs)', pixels: 4 },
  { name: '--spacing-sm', value: 'var(--spacing-sm)', pixels: 8 },
  { name: '--spacing-md', value: 'var(--spacing-md)', pixels: 12 },
  { name: '--spacing-base', value: 'var(--spacing-base)', pixels: 16 },
  { name: '--spacing-lg', value: 'var(--spacing-lg)', pixels: 20 },
  { name: '--spacing-xl', value: 'var(--spacing-xl)', pixels: 24 },
  { name: '--spacing-2xl', value: 'var(--spacing-2xl)', pixels: 32 },
  { name: '--spacing-3xl', value: 'var(--spacing-3xl)', pixels: 40 },
  { name: '--spacing-4xl', value: 'var(--spacing-4xl)', pixels: 48 },
  { name: '--spacing-5xl', value: 'var(--spacing-5xl)', pixels: 64 },
  { name: '--spacing-6xl', value: 'var(--spacing-6xl)', pixels: 80 },
  { name: '--spacing-7xl', value: 'var(--spacing-7xl)', pixels: 96 },
];

const controlSpacing = [
  { name: '--spacing-control-xs', value: 'var(--spacing-control-xs)' },
  { name: '--spacing-control-sm', value: 'var(--spacing-control-sm)' },
  { name: '--spacing-control-md', value: 'var(--spacing-control-md)' },
  { name: '--spacing-control-lg', value: 'var(--spacing-control-lg)' },
  { name: '--spacing-control-xl', value: 'var(--spacing-control-xl)' },
];

const sectionSpacing = [
  { name: '--spacing-section-sm', value: 'var(--spacing-section-sm)' },
  { name: '--spacing-section-md', value: 'var(--spacing-section-md)' },
  { name: '--spacing-section-lg', value: 'var(--spacing-section-lg)' },
  { name: '--spacing-section-xl', value: 'var(--spacing-section-xl)' },
  { name: '--spacing-section-2xl', value: 'var(--spacing-section-2xl)' },
];

export const SpacingGrid: React.FC<SpacingGridProps> = ({ onCopy, copiedToken }) => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-xl)' }}>
      {/* Base Spacing Scale */}
      <div>
        <h3 style={subTitleStyle}>Base Spacing Scale (8pt Grid)</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: 'var(--spacing-md)' }}>
          {spacingTokens.map((token) => (
            <div key={token.name} style={{ backgroundColor: 'var(--color-surface)', padding: 'var(--spacing-md)', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-border)' }}>
              <TokenCard tokenName={token.name} tokenValue={token.value} compact onCopy={onCopy} />
              <div style={{ display: 'flex', alignItems: 'flex-end', gap: 'var(--spacing-sm)', marginTop: 'var(--spacing-md)', height: '60px' }}>
                <div style={{
                  width: `${Math.max(token.pixels, 20)}px`,
                  height: `${token.pixels}px`,
                  backgroundColor: 'var(--color-primary)',
                  borderRadius: 'var(--radius-sm)',
                  transition: 'all var(--transition-normal)',
                }} />
                <span style={{ fontSize: 'var(--font-size-body-sm)', color: 'var(--color-text-tertiary)' }}>
                  {token.pixels}px
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Control Spacing */}
      <div>
        <h3 style={subTitleStyle}>Control Spacing</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 'var(--spacing-md)' }}>
          {controlSpacing.map((token) => (
            <div key={token.name} style={{ backgroundColor: 'var(--color-surface)', padding: 'var(--spacing-md)', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-border)' }}>
              <TokenCard tokenName={token.name} tokenValue={token.value} compact onCopy={onCopy} />
            </div>
          ))}
        </div>
      </div>

      {/* Section Spacing */}
      <div>
        <h3 style={subTitleStyle}>Section Spacing</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 'var(--spacing-md)' }}>
          {sectionSpacing.map((token) => (
            <div key={token.name} style={{ backgroundColor: 'var(--color-surface)', padding: 'var(--spacing-md)', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-border)' }}>
              <TokenCard tokenName={token.name} tokenValue={token.value} compact onCopy={onCopy} />
            </div>
          ))}
        </div>
      </div>

      {/* Container Widths */}
      <div>
        <h3 style={subTitleStyle}>Container Widths</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 'var(--spacing-md)' }}>
          {['--container-xs', '--container-sm', '--container-md', '--container-lg', '--container-xl', '--container-2xl', '--container-full'].map((name) => (
            <div key={name} style={{ backgroundColor: 'var(--color-surface)', padding: 'var(--spacing-md)', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-border)' }}>
              <TokenCard tokenName={name} tokenValue={`var(${name})`} compact onCopy={onCopy} />
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
