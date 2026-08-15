/**
 * Animation Showcase Section - Interactive animation triggers
 */

import React from 'react';
import { TokenCard } from './TokenCard';

interface Animation {
  name: string;
  label: string;
  class: string;
}

interface AnimationShowcaseProps {
  animations: Animation[];
  activeAnimation: string | null;
  onTrigger: (name: string) => void;
}

const durations = [
  { name: '--duration-instant', value: 'var(--duration-instant)', label: 'Instant (0ms)' },
  { name: '--duration-fastest', value: 'var(--duration-fastest)', label: 'Fastest (100ms)' },
  { name: '--duration-fast', value: 'var(--duration-fast)', label: 'Fast (150ms)' },
  { name: '--duration-normal', value: 'var(--duration-normal)', label: 'Normal (300ms)' },
  { name: '--duration-slow', value: 'var(--duration-slow)', label: 'Slow (500ms)' },
  { name: '--duration-slowest', value: 'var(--duration-slowest)', label: 'Slowest (700ms)' },
];

const easings = [
  { name: '--easing-ease-in-out', value: 'var(--easing-ease-in-out)', label: 'Ease In Out' },
  { name: '--easing-ease-out', value: 'var(--easing-ease-out)', label: 'Ease Out' },
  { name: '--easing-ease-in', value: 'var(--easing-ease-in)', label: 'Ease In' },
  { name: '--easing-bounce', value: 'var(--easing-bounce)', label: 'Bounce' },
  { name: '--easing-spring', value: 'var(--easing-spring)', label: 'Spring' },
];

export const AnimationShowcase: React.FC<AnimationShowcaseProps> = ({ animations, activeAnimation, onTrigger }) => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-xl)' }}>
      {/* Animation Triggers */}
      <div>
        <h3 style={subTitleStyle}>Click to Trigger</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: 'var(--spacing-md)' }}>
          {animations.map((anim) => (
            <button
              key={anim.name}
              onClick={() => onTrigger(anim.name)}
              style={{
                padding: 'var(--spacing-md)',
                backgroundColor: activeAnimation === anim.name ? 'var(--color-primary)' : 'var(--color-surface)',
                color: activeAnimation === anim.name ? 'var(--color-text-inverse)' : 'var(--color-text-primary)',
                border: `2px solid ${activeAnimation === anim.name ? 'var(--color-primary)' : 'var(--color-border)'}`,
                borderRadius: 'var(--radius-md)',
                cursor: 'pointer',
                fontWeight: 'var(--font-weight-medium)',
                fontSize: 'var(--font-size-body)',
                transition: 'all var(--transition-fast)',
              }}
            >
              {anim.label}
            </button>
          ))}
        </div>
      </div>

      {/* Animation Preview */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(100px, 1fr))',
        gap: 'var(--spacing-lg)',
        padding: 'var(--spacing-xl)',
        backgroundColor: 'var(--color-surface-container)',
        borderRadius: 'var(--radius-lg)',
        minHeight: '120px',
        alignItems: 'center',
      }}>
        {animations.slice(0, 7).map((anim) => (
          <div key={anim.name} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 'var(--spacing-sm)' }}>
            <div
              className={activeAnimation === anim.name ? anim.class : ''}
              style={{
                width: '48px',
                height: '48px',
                borderRadius: 'var(--radius-md)',
                backgroundColor: anim.name.includes('spin') ? 'var(--color-accent)' :
                                anim.name.includes('emergency') ? 'var(--color-error)' :
                                'var(--color-primary)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'white',
                fontSize: '20px',
              }}
            >
              {anim.name.includes('spin') ? '⟳' : anim.name.includes('pulse') ? '●' : '◆'}
            </div>
            <span style={{ fontSize: 'var(--font-size-label)', color: 'var(--color-text-tertiary)' }}>
              {anim.label}
            </span>
          </div>
        ))}
      </div>

      {/* Durations */}
      <div>
        <h3 style={subTitleStyle}>Animation Durations</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: 'var(--spacing-md)' }}>
          {durations.map((token) => (
            <div key={token.name} style={{ backgroundColor: 'var(--color-surface)', padding: 'var(--spacing-md)', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-border)' }}>
              <TokenCard tokenName={token.name} tokenValue={token.value} compact onCopy={() => {}} />
              <div style={{ marginTop: 'var(--spacing-sm)', height: '4px', backgroundColor: 'var(--color-surface-variant)', borderRadius: 'var(--radius-sm)', overflow: 'hidden' }}>
                <div style={{
                  width: token.name.includes('instant') ? '0%' :
                         token.name.includes('fastest') ? '16%' :
                         token.name.includes('fast') ? '25%' :
                         token.name.includes('normal') ? '50%' :
                         token.name.includes('slow') && !token.name.includes('slowest') ? '83%' : '100%',
                  height: '100%',
                  backgroundColor: 'var(--color-primary)',
                  borderRadius: 'var(--radius-sm)',
                }} />
              </div>
              <p style={{ fontSize: 'var(--font-size-body-sm)', color: 'var(--color-text-tertiary)', marginTop: 'var(--spacing-xs)' }}>
                {token.label}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* Easings */}
      <div>
        <h3 style={subTitleStyle}>Easing Functions</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 'var(--spacing-md)' }}>
          {easings.map((token) => (
            <div key={token.name} style={{ backgroundColor: 'var(--color-surface)', padding: 'var(--spacing-md)', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-border)' }}>
              <TokenCard tokenName={token.name} tokenValue={token.value} compact onCopy={() => {}} />
              <div style={{ marginTop: 'var(--spacing-sm)', height: '60px', position: 'relative' }}>
                <svg viewBox="0 0 100 100" style={{ width: '100%', height: '100%' }}>
                  <path
                    d="M 0 100 C 40 100, 60 0, 100 0"
                    fill="none"
                    stroke="var(--color-border)"
                    strokeWidth="2"
                  />
                  <path
                    d="M 0 100 C 20 100, 80 0, 100 0"
                    fill="none"
                    stroke="var(--color-primary)"
                    strokeWidth="2"
                  />
                </svg>
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
