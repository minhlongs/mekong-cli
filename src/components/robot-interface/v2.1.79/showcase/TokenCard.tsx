/**
 * Token Card - Reusable component for displaying and copying tokens
 */

import React, { useState, useCallback } from 'react';

interface TokenCardProps {
  tokenName: string;
  tokenValue: string;
  compact?: boolean;
  onCopy?: (name: string, value: string) => void;
}

export const TokenCard: React.FC<TokenCardProps> = ({
  tokenName,
  tokenValue,
  compact = false,
  onCopy,
}) => {
  const [copied, setCopied] = useState(false);

  const handleClick = useCallback(() => {
    if (onCopy) {
      onCopy(tokenName, tokenValue);
    }
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }, [onCopy, tokenName, tokenValue]);

  return (
    <div
      onClick={handleClick}
      style={{
        cursor: 'pointer',
        userSelect: 'none',
      }}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          handleClick();
        }
      }}
      aria-label={`Copy token ${tokenName}: ${tokenValue}`}
    >
      <div style={{
        display: 'flex',
        flexDirection: compact ? 'row' : 'column',
        alignItems: compact ? 'center' : 'flex-start',
        gap: compact ? 'var(--spacing-xs)' : 'var(--spacing-xs)',
        padding: compact ? 'var(--spacing-xs)' : 'var(--spacing-sm)',
        borderRadius: 'var(--radius-sm)',
        backgroundColor: copied ? 'var(--color-success)' : 'var(--color-surface-variant)',
        color: copied ? 'var(--color-text-inverse)' : 'var(--color-text-secondary)',
        transition: 'all var(--transition-fast)',
        border: `1px solid ${copied ? 'var(--color-success)' : 'transparent'}`,
      }}>
        <code style={{
          fontSize: compact ? 'var(--font-size-label-sm)' : 'var(--font-size-label)',
          fontWeight: 'var(--font-weight-medium)',
          color: copied ? 'inherit' : 'var(--color-text-primary)',
        }}>
          {tokenName}
        </code>
        {!compact && (
          <span style={{
            fontSize: 'var(--font-size-body-sm)',
            fontFamily: 'var(--font-family-code)',
            color: copied ? 'inherit' : 'var(--color-text-secondary)',
            wordBreak: 'break-all',
          }}>
            {tokenValue}
          </span>
        )}
        {copied && (
          <span style={{
            fontSize: 'var(--font-size-label-sm)',
            fontWeight: 'var(--font-weight-semibold)',
            marginLeft: 'auto',
          }}>
            ✓ Copied
          </span>
        )}
      </div>
    </div>
  );
};
