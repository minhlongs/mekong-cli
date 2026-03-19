/**
 * Color Palette Section - Display all color tokens with light/dark mode
 */

import React from 'react';
import { TokenCard } from './TokenCard';

interface ColorPaletteProps {
  onCopy: (name: string, value: string) => void;
  copiedToken: string | null;
}

const colorGroups = [
  {
    title: 'Surface Colors',
    tokens: [
      { name: '--color-surface', value: 'var(--color-surface)' },
      { name: '--color-surface-container', value: 'var(--color-surface-container)' },
      { name: '--color-surface-variant', value: 'var(--color-surface-variant)' },
      { name: '--color-surface-raised', value: 'var(--color-surface-raised)' },
      { name: '--color-surface-tertiary', value: 'var(--color-surface-tertiary)' },
    ],
  },
  {
    title: 'Primary Colors',
    tokens: [
      { name: '--color-primary', value: 'var(--color-primary)' },
      { name: '--color-primary-hover', value: 'var(--color-primary-hover)' },
      { name: '--color-primary-active', value: 'var(--color-primary-active)' },
      { name: '--color-primary-container', value: 'var(--color-primary-container)' },
      { name: '--color-primary-on-container', value: 'var(--color-primary-on-container)' },
    ],
  },
  {
    title: 'Secondary Colors',
    tokens: [
      { name: '--color-secondary', value: 'var(--color-secondary)' },
      { name: '--color-secondary-hover', value: 'var(--color-secondary-hover)' },
      { name: '--color-secondary-active', value: 'var(--color-secondary-active)' },
      { name: '--color-secondary-container', value: 'var(--color-secondary-container)' },
      { name: '--color-secondary-on-container', value: 'var(--color-secondary-on-container)' },
    ],
  },
  {
    title: 'Accent Colors',
    tokens: [
      { name: '--color-accent', value: 'var(--color-accent)' },
      { name: '--color-accent-hover', value: 'var(--color-accent-hover)' },
      { name: '--color-accent-active', value: 'var(--color-accent-active)' },
      { name: '--color-accent-container', value: 'var(--color-accent-container)' },
      { name: '--color-accent-on-container', value: 'var(--color-accent-on-container)' },
    ],
  },
  {
    title: 'Error Colors',
    tokens: [
      { name: '--color-error', value: 'var(--color-error)' },
      { name: '--color-error-hover', value: 'var(--color-error-hover)' },
      { name: '--color-error-active', value: 'var(--color-error-active)' },
      { name: '--color-error-container', value: 'var(--color-error-container)' },
      { name: '--color-error-on-container', value: 'var(--color-error-on-container)' },
    ],
  },
  {
    title: 'Text Colors',
    tokens: [
      { name: '--color-text-primary', value: 'var(--color-text-primary)' },
      { name: '--color-text-secondary', value: 'var(--color-text-secondary)' },
      { name: '--color-text-tertiary', value: 'var(--color-text-tertiary)' },
      { name: '--color-text-disabled', value: 'var(--color-text-disabled)' },
      { name: '--color-text-inverse', value: 'var(--color-text-inverse)' },
      { name: '--color-text-link', value: 'var(--color-text-link)' },
    ],
  },
  {
    title: 'Border Colors',
    tokens: [
      { name: '--color-border', value: 'var(--color-border)' },
      { name: '--color-border-strong', value: 'var(--color-border-strong)' },
      { name: '--color-border-subtle', value: 'var(--color-border-subtle)' },
      { name: '--color-border-focus', value: 'var(--color-border-focus)' },
    ],
  },
  {
    title: 'Utility Colors',
    tokens: [
      { name: '--color-success', value: 'var(--color-success)' },
      { name: '--color-info', value: 'var(--color-info)' },
      { name: '--color-caution', value: 'var(--color-caution)' },
      { name: '--color-critical', value: 'var(--color-critical)' },
    ],
  },
];

export const ColorPalette: React.FC<ColorPaletteProps> = ({ onCopy, copiedToken }) => {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 'var(--spacing-xl)' }}>
      {colorGroups.map((group) => (
        <div key={group.title} style={{ backgroundColor: 'var(--color-surface)', borderRadius: 'var(--radius-lg)', padding: 'var(--spacing-lg)', boxShadow: 'var(--shadow-2)' }}>
          <h3 style={{ fontSize: 'var(--font-size-title)', fontWeight: 'var(--font-weight-semibold)', marginBottom: 'var(--spacing-md)', color: 'var(--color-text-primary)' }}>
            {group.title}
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-sm)' }}>
            {group.tokens.map((token) => (
              <div key={token.name} style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-sm)' }}>
                <div style={{
                  width: '32px',
                  height: '32px',
                  borderRadius: 'var(--radius-md)',
                  backgroundColor: token.value,
                  border: '1px solid var(--color-border)',
                  flexShrink: 0,
                }} />
                <TokenCard tokenName={token.name} tokenValue={token.value} compact onCopy={onCopy} />
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
};
