/**
 * Notification Component - RaaS UX Kit v2.1.79
 * Toast notifications for robot events and alerts
 */

import React, { useEffect, useState } from 'react';
import { NotificationProps as NotificationComponentProps } from '../types/robot';
import { Icon } from '../atoms/Icon';
import { Button } from '../atoms/Button';

export const Notification: React.FC<NotificationComponentProps> = ({
  type = 'info',
  title,
  message,
  action,
  onDismiss,
  duration = 5000,
  showProgress = true,
  className = '',
}) => {
  const [progress, setProgress] = useState(100);
  const [isExiting, setIsExiting] = useState(false);

  // Type configurations
  const typeConfig = {
    info: {
      icon: (
        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <circle cx="12" cy="12" r="10" strokeWidth="2" />
          <path d="M12 16v-4M12 8h.01" strokeWidth="2" />
        </svg>
      ),
      color: 'default' as const,
      bgColor: 'bg-[var(--color-surface)]',
      borderColor: 'border-[var(--color-border)]',
    },
    success: {
      icon: (
        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <circle cx="12" cy="12" r="10" strokeWidth="2" />
          <path d="M9 12l2 2 4-4" strokeWidth="2" />
        </svg>
      ),
      color: 'success' as const,
      bgColor: 'bg-[var(--color-success-subtle)]',
      borderColor: 'border-[var(--color-success)]',
    },
    warning: {
      icon: (
        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" strokeWidth="2" />
          <path d="M12 9v4M12 17h.01" strokeWidth="2" />
        </svg>
      ),
      color: 'warning' as const,
      bgColor: 'bg-[var(--color-caution-subtle)]',
      borderColor: 'border-[var(--color-caution)]',
    },
    error: {
      icon: (
        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <circle cx="12" cy="12" r="10" strokeWidth="2" />
          <path d="M15 9l-6 6M9 9l6 6" strokeWidth="2" />
        </svg>
      ),
      color: 'error' as const,
      bgColor: 'bg-[var(--color-error-subtle)]',
      borderColor: 'border-[var(--color-error)]',
    },
    critical: {
      icon: (
        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" strokeWidth="2" />
          <path d="M12 9v4M12 17h.01" strokeWidth="2" />
        </svg>
      ),
      color: 'critical' as const,
      bgColor: 'bg-[var(--color-safety-critical-subtle)]',
      borderColor: 'border-[var(--color-safety-critical)]',
    },
  };

  const config = typeConfig[type];

  // Auto-dismiss with progress
  useEffect(() => {
    if (duration <= 0) return;

    const startTime = Date.now();
    const interval = setInterval(() => {
      const elapsed = Date.now() - startTime;
      const remaining = Math.max(0, 100 - (elapsed / duration) * 100);
      setProgress(remaining);

      if (remaining <= 0) {
        clearInterval(interval);
        handleDismiss();
      }
    }, 50);

    return () => clearInterval(interval);
  }, [duration]);

  const handleDismiss = () => {
    setIsExiting(true);
    setTimeout(() => {
      onDismiss?.();
    }, 200);
  };

  return (
    <div
      className={`
        relative flex items-start gap-3 p-4
        bg-[var(--color-surface)]
        border-l-4 rounded-[var(--radius-md)]
        shadow-lg
        min-w-[300px] max-w-[450px]
        transition-all duration-200
        ${isExiting ? 'opacity-0 translate-x-full' : 'opacity-100 translate-x-0'}
        ${config.borderColor}
        ${className}
      `}
      role="alert"
      aria-live={type === 'error' || type === 'critical' ? 'assertive' : 'polite'}
    >
      {/* Icon */}
      <div className="flex-shrink-0">
        <Icon size="lg" color={config.color}>
          {config.icon}
        </Icon>
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        {title && (
          <h4 className="text-sm font-semibold text-[var(--color-text-primary)] mb-1">
            {title}
          </h4>
        )}
        <p className="text-sm text-[var(--color-text-secondary)] break-words">
          {message}
        </p>

        {/* Action Button */}
        {action && (
          <div className="mt-2">
            <Button
              variant={action.variant || 'primary'}
              size="sm"
              onClick={action.onClick}
            >
              {action.label}
            </Button>
          </div>
        )}
      </div>

      {/* Close Button */}
      <button
        onClick={handleDismiss}
        className="flex-shrink-0 p-1 text-[var(--color-text-tertiary)] hover:text-[var(--color-text-secondary)]"
        aria-label="Dismiss notification"
      >
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path d="M6 18L18 6M6 6l12 12" strokeWidth="2" />
        </svg>
      </button>

      {/* Progress Bar */}
      {showProgress && duration > 0 && (
        <div
          className={`absolute bottom-0 left-0 h-1 ${
            type === 'error' || type === 'critical'
              ? 'bg-[var(--color-error)]'
              : 'bg-[var(--color-primary)]'
          } transition-all duration-100`}
          style={{ width: `${progress}%` }}
        />
      )}
    </div>
  );
};

// ============================================
// Notification Container
// ============================================

export interface NotificationContainerProps {
  position?: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left' | 'top-center' | 'bottom-center';
  children: React.ReactNode;
  className?: string;
}

export const NotificationContainer: React.FC<NotificationContainerProps> = ({
  position = 'top-right',
  children,
  className = '',
}) => {
  const positionClasses = {
    'top-right': 'top-0 right-0',
    'top-left': 'top-0 left-0',
    'top-center': 'top-0 left-1/2 -translate-x-1/2',
    'bottom-right': 'bottom-0 right-0',
    'bottom-left': 'bottom-0 left-0',
    'bottom-center': 'bottom-0 left-1/2 -translate-x-1/2',
  };

  return (
    <div
      className={`
        fixed z-[9999] p-4 flex flex-col gap-2
        ${positionClasses[position]}
        ${className}
      `}
      role="region"
      aria-label="Notifications"
    >
      {children}
    </div>
  );
};

export default Notification;
