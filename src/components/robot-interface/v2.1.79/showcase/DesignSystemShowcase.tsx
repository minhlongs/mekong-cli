/**
 * Design System Showcase - RaaS UX Kit v2.1.79
 * Visual preview of all design tokens with interactive features
 */

import React, { useState, useCallback, useEffect } from 'react';
import { Button, StatusBadge } from '../../atoms';
import { ColorPalette } from './ColorPalette';
import { TypographyScale } from './TypographyScale';
import { SpacingGrid } from './SpacingGrid';
import { ShadowSamples } from './ShadowSamples';
import { BorderRadiusSamples } from './BorderRadiusSamples';
import { AnimationShowcase } from './AnimationShowcase';
import { StatusIndicators } from './StatusIndicators';
import { TokenCard } from './TokenCard';

export interface DesignSystemShowcaseProps {
  className?: string;
}

export const DesignSystemShowcase: React.FC<DesignSystemShowcaseProps> = ({ className = '' }) => {
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [activeAnimation, setActiveAnimation] = useState<string | null>(null);
  const [copiedToken, setCopiedToken] = useState<string | null>(null);

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', isDarkMode ? 'dark' : 'light');
  }, [isDarkMode]);

  const handleCopyToken = useCallback((tokenName: string, tokenValue: string) => {
    navigator.clipboard.writeText(tokenValue);
    setCopiedToken(tokenName);
    setTimeout(() => setCopiedToken(null), 2000);
  }, []);

  const triggerAnimation = useCallback((animName: string) => {
    setActiveAnimation(animName);
    setTimeout(() => setActiveAnimation(null), 2000);
  }, []);

  const animations = [
    { name: 'pulse', label: 'Pulse', class: 'animate-pulse' },
    { name: 'spin', label: 'Spin', class: 'animate-spin' },
    { name: 'shake', label: 'Shake', class: 'animate-shake' },
    { name: 'bounce', label: 'Bounce', class: 'animate-bounce' },
    { name: 'pulse-glow', label: 'Pulse Glow', class: 'animate-pulse-glow' },
    { name: 'pulse-emergency', label: 'Emergency', class: 'animate-pulse-emergency' },
    { name: 'pulse-badge', label: 'Pulse Badge', class: 'animate-pulse-badge' },
    { name: 'fade-in', label: 'Fade In', class: 'animate-fade-in' },
    { name: 'slide-in-top', label: 'Slide Top', class: 'animate-slide-in-from-top' },
    { name: 'slide-in-bottom', label: 'Slide Bottom', class: 'animate-slide-in-from-bottom' },
    { name: 'scale-in', label: 'Scale In', class: 'animate-scale-in' },
  ];

  return (
    <div className={`design-system-showcase ${className}`} style={{
      fontFamily: 'var(--font-family-base)',
      backgroundColor: 'var(--color-surface)',
      color: 'var(--color-text-primary)',
      minHeight: '100vh',
      padding: 'var(--spacing-2xl)',
    }}>
      {/* Header */}
      <header style={{
        marginBottom: 'var(--spacing-4xl)',
        paddingBottom: 'var(--spacing-xl)',
        borderBottom: '1px solid var(--color-border)',
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--spacing-lg)' }}>
          <div>
            <h1 style={{ fontSize: 'var(--font-size-display)', fontWeight: 'var(--font-weight-bold)', color: 'var(--color-text-primary)', marginBottom: 'var(--spacing-xs)' }}>
              Robot Interface Components
            </h1>
            <p style={{ fontSize: 'var(--font-size-body-lg)', color: 'var(--color-text-secondary)' }}>
              Design System Showcase v2.1.79
            </p>
          </div>
          <Button
            variant="secondary"
            onClick={() => setIsDarkMode(!isDarkMode)}
            icon={isDarkMode ? '☀️' : '🌙'}
          >
            {isDarkMode ? 'Light' : 'Dark'}
          </Button>
        </div>
        <TokenCard tokenName="--version" tokenValue="2.1.79" />
      </header>

      {/* Color Palette */}
      <section style={sectionStyle}>
        <h2 style={sectionTitleStyle}>Color Palette</h2>
        <ColorPalette onCopy={handleCopyToken} copiedToken={copiedToken} />
      </section>

      {/* Typography */}
      <section style={sectionStyle}>
        <h2 style={sectionTitleStyle}>Typography Scale</h2>
        <TypographyScale onCopy={handleCopyToken} copiedToken={copiedToken} />
      </section>

      {/* Spacing */}
      <section style={sectionStyle}>
        <h2 style={sectionTitleStyle}>Spacing (8pt Grid)</h2>
        <SpacingGrid onCopy={handleCopyToken} copiedToken={copiedToken} />
      </section>

      {/* Shadows */}
      <section style={sectionStyle}>
        <h2 style={sectionTitleStyle}>Shadows & Elevation</h2>
        <ShadowSamples onCopy={handleCopyToken} copiedToken={copiedToken} />
      </section>

      {/* Border Radius */}
      <section style={sectionStyle}>
        <h2 style={sectionTitleStyle}>Border Radius</h2>
        <BorderRadiusSamples onCopy={handleCopyToken} copiedToken={copiedToken} />
      </section>

      {/* Animations */}
      <section style={sectionStyle}>
        <h2 style={sectionTitleStyle}>Animation Demonstrations</h2>
        <p style={{ marginBottom: 'var(--spacing-lg)', color: 'var(--color-text-secondary)' }}>
          Click to trigger animations
        </p>
        <AnimationShowcase animations={animations} activeAnimation={activeAnimation} onTrigger={triggerAnimation} />
      </section>

      {/* Robot Status Indicators */}
      <section style={sectionStyle}>
        <h2 style={sectionTitleStyle}>Robot Status Indicators</h2>
        <StatusIndicators onCopy={handleCopyToken} copiedToken={copiedToken} />
      </section>

      {/* Footer */}
      <footer style={{ marginTop: 'var(--spacing-5xl)', paddingTop: 'var(--spacing-xl)', borderTop: '1px solid var(--color-border)', textAlign: 'center', color: 'var(--color-text-tertiary)' }}>
        <p>RaaS UX Kit v2.1.79 • Built with React, TypeScript & Design Tokens</p>
        <p style={{ fontSize: 'var(--font-size-body-sm)', marginTop: 'var(--spacing-xs)' }}>
          Click any token value to copy
        </p>
      </footer>
    </div>
  );
};

const sectionStyle: React.CSSProperties = {
  marginBottom: 'var(--spacing-5xl)',
  padding: 'var(--spacing-xl)',
  borderRadius: 'var(--radius-card)',
  backgroundColor: 'var(--color-surface-container)',
  boxShadow: 'var(--shadow-2)',
};

const sectionTitleStyle: React.CSSProperties = {
  fontSize: 'var(--font-size-headline-lg)',
  fontWeight: 'var(--font-weight-bold)',
  color: 'var(--color-text-primary)',
  marginBottom: 'var(--spacing-xl)',
  paddingBottom: 'var(--spacing-md)',
  borderBottom: '2px solid var(--color-primary)',
};

export default DesignSystemShowcase;
