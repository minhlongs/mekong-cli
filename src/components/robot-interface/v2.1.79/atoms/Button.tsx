/**
 * Button Component - RaaS UX Kit v2.1.79
 * Interactive button for robot control operations
 */

import React, { useState, useCallback } from 'react';
import { ButtonProps } from '../types/robot';

export const Button: React.FC<ButtonProps> = ({
  variant = 'primary',
  size = 'md',
  isLoading = false,
  isDisabled = false,
  icon,
  confirmRequired = false,
  confirmMessage,
  children,
  className = '',
  onClick,
  type = 'button',
  ...props
}) => {
  const [awaitingConfirmation, setAwaitingConfirmation] = useState(false);

  // Size mappings
  const sizeClasses = {
    sm: 'h-8 px-3 text-xs',
    md: 'h-10 px-4 text-sm',
    lg: 'h-12 px-6 text-base',
    xl: 'h-16 px-8 text-lg',
  };

  // Variant mappings using CSS custom properties
  const variantClasses = {
    primary:
      'bg-[var(--color-primary)] text-[var(--color-text-inverse)] hover:bg-[var(--color-primary-hover)] active:bg-[var(--color-primary-active)]',
    secondary:
      'bg-[var(--color-surface-tertiary)] text-[var(--color-text-primary)] hover:bg-[var(--color-surface-variant)] active:bg-[var(--color-surface-container)]',
    outline:
      'bg-transparent text-[var(--color-text-primary)] border border-[var(--color-border)] hover:bg-[var(--color-surface-tertiary)] active:bg-[var(--color-surface-container)]',
    ghost:
      'bg-transparent text-[var(--color-text-secondary)] hover:bg-[var(--color-surface-tertiary)] hover:text-[var(--color-text-primary)] active:bg-[var(--color-surface-container)]',
    danger:
      'bg-[var(--color-error)] text-[var(--color-text-inverse)] hover:bg-[var(--color-error-hover)] active:bg-[var(--color-error-active)]',
    'emergency-stop':
      'bg-[var(--color-safety-critical)] text-[var(--color-text-inverse)] hover:bg-[var(--color-safety-critical-hover)] active:bg-[var(--color-safety-critical)] border-2 border-white animate-pulse-emergency',
  };

  // Emergency stop requires XL size
  const finalSize = variant === 'emergency-stop' ? 'xl' : size;

  const handleClick = useCallback(
    (e: React.MouseEvent<HTMLButtonElement>) => {
      if (confirmRequired && !awaitingConfirmation) {
        e.preventDefault();
        setAwaitingConfirmation(true);
        // Reset confirmation state after 3 seconds
        setTimeout(() => setAwaitingConfirmation(false), 3000);
        return;
      }

      if (!isDisabled && !isLoading) {
        onClick?.(e);
      }
    },
    [confirmRequired, awaitingConfirmation, isDisabled, isLoading, onClick]
  );

  // Button is disabled if: explicitly disabled, loading, or awaiting double-confirmation for E-stop
  const isActuallyDisabled =
    isDisabled || isLoading || (confirmRequired && awaitingConfirmation);

  return (
    <button
      type={type}
      className={`
        inline-flex items-center justify-center gap-2
        font-medium rounded-[var(--radius-button)]
        transition-all duration-150 ease-out
        focus:outline-none focus:ring-2 focus:ring-[var(--color-focus-ring)] focus:ring-offset-2
        disabled:opacity-40 disabled:cursor-not-allowed
        ${sizeClasses[finalSize]}
        ${variantClasses[variant]}
        ${className}
      `}
      disabled={isActuallyDisabled}
      onClick={handleClick}
      aria-disabled={isActuallyDisabled}
      aria-label={children ? undefined : 'button'}
      {...props}
    >
      {isLoading ? (
        <svg
          className="animate-spin h-5 w-5"
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
        <span className="flex-shrink-0">{icon}</span>
      ) : null}

      {children && <span>{children}</span>}

      {confirmRequired && awaitingConfirmation && (
        <span className="text-xs font-semibold animate-pulse">
          CLICK AGAIN TO CONFIRM
        </span>
      )}
    </button>
  );
};

export default Button;
