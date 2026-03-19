/**
 * CTA Button - RaaS UX Kit v2.1.79
 * High-converting Call-to-Action button for marketing and landing pages
 *
 * Optimized for: Click-through rates, visual prominence, conversion funnels
 */

import React, { useState, useCallback } from 'react';

/**
 * CTA Button Variants
 * - primary: Main conversion action (Get Started, Subscribe)
 * - secondary: Alternative action (Learn More, View Pricing)
 * - gradient: Premium/highlight action (Pro, Enterprise)
 * - outline: Low-friction action (Watch Demo, See Features)
 * - success: Positive confirmation (Activate, Start Free Trial, Enable)
 */
const VARIANTS = {
  primary: {
    bg: 'var(--color-primary)',
    hover: 'var(--color-primary-hover)',
    active: 'var(--color-primary-active)',
    text: 'var(--color-text-inverse)',
    shadow: 'var(--shadow-3)',
  },
  secondary: {
    bg: 'var(--color-secondary)',
    hover: 'var(--color-secondary-hover)',
    active: 'var(--color-secondary-active)',
    text: 'var(--color-text-inverse)',
    shadow: 'var(--shadow-2)',
  },
  gradient: {
    bg: 'linear-gradient(135deg, var(--color-primary) 0%, var(--color-accent) 100%)',
    hover: 'linear-gradient(135deg, var(--color-primary-hover) 0%, var(--color-accent-hover) 100%)',
    active: 'linear-gradient(135deg, var(--color-primary-active) 0%, var(--color-accent-active) 100%)',
    text: 'var(--color-text-inverse)',
    shadow: 'var(--shadow-4)',
  },
  outline: {
    bg: 'transparent',
    hover: 'var(--color-surface-tertiary)',
    active: 'var(--color-surface-container)',
    text: 'var(--color-text-primary)',
    border: 'var(--color-border-strong)',
    shadow: 'none',
  },
  success: {
    bg: 'var(--color-success)',
    hover: 'var(--color-success-hover, var(--color-success))',
    active: 'var(--color-success-active, var(--color-success))',
    text: 'var(--color-text-inverse)',
    shadow: 'var(--shadow-3)',
  },
};

/**
 * Size Mappings
 */
const SIZES = {
  sm: {
    height: 'h-10',
    paddingX: 'px-5',
    fontSize: 'text-sm',
    iconSize: 'h-4 w-4',
  },
  md: {
    height: 'h-12',
    paddingX: 'px-7',
    fontSize: 'text-base',
    iconSize: 'h-5 w-5',
  },
  lg: {
    height: 'h-14',
    paddingX: 'px-9',
    fontSize: 'text-lg',
    iconSize: 'h-6 w-6',
  },
  xl: {
    height: 'h-16',
    paddingX: 'px-11',
    fontSize: 'text-xl',
    iconSize: 'h-7 w-7',
  },
};

/**
 * CTA Button Component
 *
 * @param {Object} props
 * @param {'primary'|'secondary'|'gradient'|'outline'} props.variant - Visual style
 * @param {'sm'|'md'|'lg'|'xl'} props.size - Button size
 * @param {boolean} props.isLoading - Loading state
 * @param {boolean} props.fullWidth - Full width button
 * @param {string} props.icon - Optional leading icon
 * @param {string} props.className - Additional CSS classes
 * @param {Function} props.onClick - Click handler
 * @param {React.ReactNode} props.children - Button text
 */
export const CTAButton = ({
  variant = 'primary',
  size = 'lg',
  isLoading = false,
  fullWidth = false,
  icon,
  className = '',
  onClick,
  children,
  ...props
}) => {
  const [isHovered, setIsHovered] = useState(false);

  const variantStyles = VARIANTS[variant];
  const sizeStyles = SIZES[size];

  const handleClick = useCallback(
    (e) => {
      if (!isLoading) {
        onClick?.(e);
      }
    },
    [isLoading, onClick]
  );

  const baseStyles = `
    inline-flex items-center justify-center gap-3
    font-semibold rounded-[var(--radius-button)]
    transition-all duration-200 ease-out
    focus:outline-none focus:ring-2 focus:ring-[var(--color-focus-ring)] focus:ring-offset-2
    disabled:opacity-60 disabled:cursor-not-allowed
    ${sizeStyles.height}
    ${sizeStyles.paddingX}
    ${sizeStyles.fontSize}
    ${fullWidth ? 'w-full' : ''}
    ${variantStyles.shadow !== 'none' ? `shadow-[${variantStyles.shadow}]` : ''}
    ${isHovered && !isLoading ? 'transform scale-[1.02]' : ''}
    ${className}
  `;

  const variantClass = variant === 'outline'
    ? `border-2 border-[var(--color-border-strong)] text-[var(--color-text-primary)] hover:bg-[var(--color-surface-tertiary)] active:bg-[var(--color-surface-container)]`
    : `text-[${variantStyles.text}] hover:brightness-110 active:brightness-90`;

  const backgroundStyle = variant === 'outline'
    ? {}
    : { background: variantStyles.bg };

  return (
    <button
      type="button"
      className={baseStyles}
      style={backgroundStyle}
      disabled={isLoading}
      onClick={handleClick}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      aria-disabled={isLoading}
      aria-busy={isLoading}
      {...props}
    >
      {isLoading ? (
        <svg
          className={`animate-spin ${sizeStyles.iconSize}`}
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
          />
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
          />
        </svg>
      ) : icon ? (
        <span className={sizeStyles.iconSize}>{icon}</span>
      ) : null}

      {children && <span className="whitespace-nowrap">{children}</span>}
    </button>
  );
};

export default CTAButton;
