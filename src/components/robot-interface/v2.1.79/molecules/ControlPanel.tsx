/**
 * ControlPanel Component - RaaS UX Kit v2.1.79
 * Robot control panel with action buttons and status display
 */

import React from 'react';
import { ControlPanelProps } from '../types/robot';
import { Button } from '../atoms/Button';
import { StatusBadge } from '../atoms/StatusBadge';
import { Icon } from '../atoms/Icon';

export const ControlPanel: React.FC<ControlPanelProps> = ({
  robotStatus = 'offline',
  isPlaying = false,
  isPaused = false,
  isLoading = false,
  emergencyArmed = false,
  onPlay,
  onPause,
  onStop,
  onEmergencyStop,
  onRestart,
  disabled = false,
  className = '',
}) => {
  return (
    <div
      className={`
        flex flex-col gap-4 p-4
        bg-[var(--color-surface)]
        border border-[var(--color-border)]
        rounded-[var(--radius-lg)]
        ${className}
      `}
      role="region"
      aria-label="Robot control panel"
    >
      {/* Status Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Icon
            size="lg"
            color={
              robotStatus === 'error' ? 'error' :
              robotStatus === 'warning' ? 'warning' :
              robotStatus === 'online' ? 'success' : 'secondary'
            }
          >
            {robotStatus === 'online' ? (
              <circle cx="12" cy="12" r="10" />
            ) : robotStatus === 'error' ? (
              <path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
            ) : (
              <circle cx="12" cy="12" r="10" />
            )}
          </Icon>
          <div>
            <h3 className="text-sm font-semibold text-[var(--color-text-primary)]">
              Robot Status
            </h3>
            <p className="text-xs text-[var(--color-text-tertiary)]">
              {emergencyArmed ? 'EMERGENCY ARMED' : 'System ready'}
            </p>
          </div>
        </div>
        <StatusBadge variant={robotStatus} size="md" isDropdown>
          {robotStatus.charAt(0).toUpperCase() + robotStatus.slice(1)}
        </StatusBadge>
      </div>

      {/* Control Buttons */}
      <div className="grid grid-cols-2 gap-2">
        {/* Play/Resume Button */}
        <Button
          variant="primary"
          size="md"
          onClick={onPlay}
          disabled={disabled || isLoading || isPlaying || robotStatus !== 'online'}
          icon={
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
              <polygon points="5,3 19,12 5,21" />
            </svg>
          }
        >
          {isPaused ? 'Resume' : 'Start'}
        </Button>

        {/* Pause Button */}
        <Button
          variant="secondary"
          size="md"
          onClick={onPause}
          disabled={disabled || isLoading || !isPlaying || isPaused}
          icon={
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
              <rect x="6" y="4" width="4" height="16" />
              <rect x="14" y="4" width="4" height="16" />
            </svg>
          }
        >
          Pause
        </Button>

        {/* Stop Button */}
        <Button
          variant="outline"
          size="md"
          onClick={onStop}
          disabled={disabled || isLoading || (!isPlaying && !isPaused)}
          icon={
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
              <rect x="4" y="4" width="16" height="16" />
            </svg>
          }
        >
          Stop
        </Button>

        {/* Restart Button */}
        <Button
          variant="ghost"
          size="md"
          onClick={onRestart}
          disabled={disabled || isLoading}
          icon={
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path d="M23 4v6h-6" strokeWidth="2" />
              <path d="M20.49 15a9 9 0 11-2.12-9.36L23 10" strokeWidth="2" />
            </svg>
          }
        >
          Restart
        </Button>
      </div>

      {/* Emergency Stop Button */}
      <div className="mt-2">
        <Button
          variant="emergency-stop"
          size="xl"
          onClick={onEmergencyStop}
          disabled={disabled || isLoading}
          confirmRequired={true}
          confirmMessage="Click again to activate emergency stop"
          className="w-full"
          icon={
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <circle cx="12" cy="12" r="10" strokeWidth="2" />
              <path d="M15 9l-6 6M9 9l6 6" strokeWidth="2" />
            </svg>
          }
        >
          EMERGENCY STOP
        </Button>
      </div>
    </div>
  );
};

export default ControlPanel;
