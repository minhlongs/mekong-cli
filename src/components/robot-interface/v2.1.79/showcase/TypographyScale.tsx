/**
 * Typography Scale Section - Display all font tokens
 */

import React from 'react';
import { TokenCard } from './TokenCard';

interface TypographyScaleProps {
  onCopy: (name: string, value: string) => void;
  copiedToken: string | null;
}

const fontSizes = [
  { name: '--font-size-display-xl', value: 'var(--font-size-display-xl)', sample: 'Display XL' },
  { name: '--font-size-display-lg', value: 'var(--font-size-display-lg)', sample: 'Display LG' },
  { name: '--font-size-display', value: 'var(--font-size-display)', sample: 'Display' },
  { name: '--font-size-display-sm', value: 'var(--font-size-display-sm)', sample: 'Display SM' },
  { name: '--font-size-headline-xl', value: 'var(--font-size-headline-xl)', sample: 'Headline XL' },
  { name: '--font-size-headline-lg', value: 'var(--font-size-headline-lg)', sample: 'Headline LG' },
  { name: '--font-size-headline', value: 'var(--font-size-headline)', sample: 'Headline' },
  { name: '--font-size-headline-md', value: 'var(--font-size-headline-md)', sample: 'Headline MD' },
  { name: '--font-size-headline-sm', value: 'var(--font-size-headline-sm)', sample: 'Headline SM' },
  { name: '--font-size-title-lg', value: 'var(--font-size-title-lg)', sample: 'Title LG' },
  { name: '--font-size-title', value: 'var(--font-size-title)', sample: 'Title' },
  { name: '--font-size-title-sm', value: 'var(--font-size-title-sm)', sample: 'Title SM' },
  { name: '--font-size-body-lg', value: 'var(--font-size-body-lg)', sample: 'Body LG - The quick brown fox jumps over the lazy dog.' },
  { name: '--font-size-body', value: 'var(--font-size-body)', sample: 'Body - The quick brown fox jumps over the lazy dog.' },
  { name: '--font-size-body-sm', value: 'var(--font-size-body-sm)', sample: 'Body SM - The quick brown fox jumps over the lazy dog.' },
  { name: '--font-size-label-lg', value: 'var(--font-size-label-lg)', sample: 'Label LG' },
  { name: '--font-size-label', value: 'var(--font-size-label)', sample: 'Label' },
  { name: '--font-size-label-sm', value: 'var(--font-size-label-sm)', sample: 'Label SM' },
];

const lineHeights = [
  { name: '--line-height-none', value: 'var(--line-height-none)' },
  { name: '--line-height-tight', value: 'var(--line-height-tight)' },
  { name: '--line-height-snug', value: 'var(--line-height-snug)' },
  { name: '--line-height-normal', value: 'var(--line-height-normal)' },
  { name: '--line-height-relaxed', value: 'var(--line-height-relaxed)' },
  { name: '--line-height-loose', value: 'var(--line-height-loose)' },
];

const fontWeights = [
  { name: '--font-weight-regular', value: 'var(--font-weight-regular)', sample: 'Regular (400)' },
  { name: '--font-weight-medium', value: 'var(--font-weight-medium)', sample: 'Medium (500)' },
  { name: '--font-weight-semibold', value: 'var(--font-weight-semibold)', sample: 'Semibold (600)' },
  { name: '--font-weight-bold', value: 'var(--font-weight-bold)', sample: 'Bold (700)' },
];

const fontFamilies = [
  { name: '--font-family-primary', value: 'var(--font-family-primary)', sample: 'Primary Font - Inter' },
  { name: '--font-family-secondary', value: 'var(--font-family-secondary)', sample: 'Secondary Font - be Vietnam Pro' },
  { name: '--font-family-mono', value: 'var(--font-family-mono)', sample: 'Monospace - JetBrains Mono' },
  { name: '--font-family-code', value: 'var(--font-family-code)', sample: 'Code - const x = 10;' },
];

export const TypographyScale: React.FC<TypographyScaleProps> = ({ onCopy, copiedToken }) => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-xl)' }}>
      {/* Font Sizes */}
      <div>
        <h3 style={subTitleStyle}>Font Sizes</h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-md)' }}>
          {fontSizes.map((token) => (
            <div key={token.name} style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-md)', flexWrap: 'wrap' }}>
              <div style={{ minWidth: '200px' }}>
                <TokenCard tokenName={token.name} tokenValue={token.value} compact onCopy={onCopy} />
              </div>
              <span style={{ fontSize: token.value, color: 'var(--color-text-primary)' }}>{token.sample}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Line Heights */}
      <div>
        <h3 style={subTitleStyle}>Line Heights</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 'var(--spacing-md)' }}>
          {lineHeights.map((token) => (
            <div key={token.name} style={{ backgroundColor: 'var(--color-surface)', padding: 'var(--spacing-md)', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-border)' }}>
              <TokenCard tokenName={token.name} tokenValue={token.value} compact onCopy={onCopy} />
              <p style={{ lineHeight: token.value, marginTop: 'var(--spacing-sm)', color: 'var(--color-text-secondary)' }}>
                Line height {token.name.replace('--line-height-', '')}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* Font Weights */}
      <div>
        <h3 style={subTitleStyle}>Font Weights</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 'var(--spacing-md)' }}>
          {fontWeights.map((token) => (
            <div key={token.name} style={{ backgroundColor: 'var(--color-surface)', padding: 'var(--spacing-md)', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-border)' }}>
              <TokenCard tokenName={token.name} tokenValue={token.value} compact onCopy={onCopy} />
              <p style={{ fontWeight: token.value.replace('var(--', '').replace(')', ''), marginTop: 'var(--spacing-sm)', color: 'var(--color-text-primary)' }}>
                {token.sample}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* Font Families */}
      <div>
        <h3 style={subTitleStyle}>Font Families</h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-md)' }}>
          {fontFamilies.map((token) => (
            <div key={token.name} style={{ backgroundColor: 'var(--color-surface)', padding: 'var(--spacing-md)', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-border)' }}>
              <TokenCard tokenName={token.name} tokenValue={token.value} onCopy={onCopy} />
              <p style={{ fontFamily: token.value, marginTop: 'var(--spacing-sm)', color: 'var(--color-text-primary)' }}>
                {token.sample}
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
  marginTop: 'var(--spacing-lg)',
};
