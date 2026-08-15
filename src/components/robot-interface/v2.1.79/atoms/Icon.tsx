/**
 * Icon Component - RaaS UX Kit v2.1.79
 * Unified visual language for robot interface communication
 */

import React from 'react';
import { IconProps, IconSize, IconColor } from '../types/robot';

// Size mappings
const sizeMap: Record<IconSize, string> = {
  xs: 'w-3 h-3', // 12px
  sm: 'w-4 h-4', // 16px
  md: 'w-5 h-5', // 20px
  lg: 'w-6 h-6', // 24px
  xl: 'w-8 h-8', // 32px
  '2xl': 'w-12 h-12', // 48px
};

// Color mappings using CSS custom properties
const colorMap: Record<IconColor, string> = {
  default: 'text-[var(--color-text-primary)]',
  secondary: 'text-[var(--color-text-secondary)]',
  success: 'text-[var(--color-success)]',
  warning: 'text-[var(--color-caution)]',
  error: 'text-[var(--color-error)]',
  critical: 'text-[var(--color-safety-critical)]',
};

// Animation classes
const animationMap: Record<string, string> = {
  pulse: 'animate-pulse',
  spin: 'animate-spin',
  bounce: 'animate-bounce',
  shake: 'animate-shake',
};

export const Icon: React.FC<IconProps & { path?: string }> = ({
  size = 'md',
  color = 'default',
  isAnimated = false,
  animation,
  className = '',
  path,
  children,
  ...props
}) => {
  const animationClass = isAnimated
    ? animation || 'animate-pulse'
    : undefined;

  return (
    <svg
      className={`
        inline-flex flex-shrink-0
        transition-all duration-150
        ${sizeMap[size]}
        ${colorMap[color]}
        ${animationClass ? animationMap[animationClass] : ''}
        ${className}
      `}
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      viewBox="0 0 24 24"
      {...props}
    >
      {children || path}
    </svg>
  );
};

// ============================================
// Robot Status Icons
// ============================================

export const RobotOnlineIcon: React.FC<IconProps> = (props) => (
  <Icon {...props}>
    <circle cx="12" cy="12" r="10" />
    <path d="M9 12l2 2 4-4" />
  </Icon>
);

export const RobotOfflineIcon: React.FC<IconProps> = (props) => (
  <Icon {...props}>
    <circle cx="12" cy="12" r="10" />
    <path d="M15 9l-6 6M9 9l6 6" />
  </Icon>
);

export const RobotChargingIcon: React.FC<IconProps> = (props) => (
  <Icon {...props}>
    <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" />
  </Icon>
);

export const RobotBatteryLowIcon: React.FC<IconProps> = (props) => (
  <Icon {...props}>
    <rect x="3" y="6" width="14" height="12" rx="2" />
    <path d="M7 10h4" />
    <path d="M21 10v4" />
    <path d="M17 10l-2-2M17 14l-2 2" />
  </Icon>
);

export const RobotErrorIcon: React.FC<IconProps> = (props) => (
  <Icon {...props} color="error">
    <path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
    <path d="M12 9v4M12 17h.01" />
  </Icon>
);

export const RobotWarningIcon: React.FC<IconProps> = (props) => (
  <Icon {...props} color="warning">
    <circle cx="12" cy="12" r="10" />
    <path d="M12 8v4M12 16h.01" />
  </Icon>
);

// ============================================
// Action Icons
// ============================================

export const PlayIcon: React.FC<IconProps> = (props) => (
  <Icon {...props}>
    <polygon points="5,3 19,12 5,21" fill="currentColor" stroke="none" />
  </Icon>
);

export const PauseIcon: React.FC<IconProps> = (props) => (
  <Icon {...props}>
    <rect x="6" y="4" width="4" height="16" fill="currentColor" stroke="none" />
    <rect x="14" y="4" width="4" height="16" fill="currentColor" stroke="none" />
  </Icon>
);

export const StopIcon: React.FC<IconProps> = (props) => (
  <Icon {...props}>
    <rect x="4" y="4" width="16" height="16" fill="currentColor" stroke="none" />
  </Icon>
);

export const RestartIcon: React.FC<IconProps> = (props) => (
  <Icon {...props}>
    <path d="M23 4v6h-6" />
    <path d="M20.49 15a9 9 0 11-2.12-9.36L23 10" />
  </Icon>
);

export const AbortIcon: React.FC<IconProps> = (props) => (
  <Icon {...props} color="error">
    <circle cx="12" cy="12" r="10" />
    <path d="M15 9l-6 6M9 9l6 6" />
  </Icon>
);

export const UploadIcon: React.FC<IconProps> = (props) => (
  <Icon {...props}>
    <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" />
    <polyline points="17,8 12,3 7,8" />
    <line x1="12" y1="3" x2="12" y2="15" />
  </Icon>
);

export const DownloadIcon: React.FC<IconProps> = (props) => (
  <Icon {...props}>
    <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" />
    <polyline points="7,10 12,15 17,10" />
    <line x1="12" y1="15" x2="12" y2="3" />
  </Icon>
);

export const SyncIcon: React.FC<IconProps> = (props) => (
  <Icon {...props}>
    <path d="M23 4v6h-6" />
    <path d="M1 20v-6h6" />
    <path d="M20.49 9A9 9 0 005.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 013.51 15" />
  </Icon>
);

export const RefreshIcon: React.FC<IconProps> = (props) => (
  <Icon {...props}>
    <path d="M23 4v6h-6" />
    <path d="M1 20v-6h6" />
    <path d="M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15" />
  </Icon>
);

export const EditIcon: React.FC<IconProps> = (props) => (
  <Icon {...props}>
    <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7" />
    <path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z" />
  </Icon>
);

export const DeleteIcon: React.FC<IconProps> = (props) => (
  <Icon {...props}>
    <polyline points="3,6 5,6 21,6" />
    <path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2" />
  </Icon>
);

// ============================================
// Navigation Icons
// ============================================

export const HomeIcon: React.FC<IconProps> = (props) => (
  <Icon {...props}>
    <path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z" />
    <polyline points="9,22 9,12 15,12 15,22" />
  </Icon>
);

export const RobotsIcon: React.FC<IconProps> = (props) => (
  <Icon {...props}>
    <rect x="3" y="11" width="18" height="10" rx="2" />
    <circle cx="12" cy="5" r="2" />
    <path d="M12 7v4M8 21v-2M16 21v-2" />
  </Icon>
);

export const MissionsIcon: React.FC<IconProps> = (props) => (
  <Icon {...props}>
    <polygon points="3,11 22,2 13,21 11,13" />
  </Icon>
);

export const SettingsIcon: React.FC<IconProps> = (props) => (
  <Icon {...props}>
    <circle cx="12" cy="12" r="3" />
    <path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-2 2 2 2 0 01-2-2v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83 0 2 2 0 010-2.83l.06-.06a1.65 1.65 0 00.33-1.82 1.65 1.65 0 00-1.51-1H3a2 2 0 01-2-2 2 2 0 012-2h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 010-2.83 2 2 0 012.83 0l.06.06a1.65 1.65 0 001.82.33H9a1.65 1.65 0 001-1.51V3a2 2 0 012-2 2 2 0 012 2v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 0 2 2 0 010 2.83l-.06.06a1.65 1.65 0 00-.33 1.82V9a1.65 1.65 0 001.51 1H21a2 2 0 012 2 2 2 0 01-2 2h-.09a1.65 1.65 0 00-1.51 1z" />
  </Icon>
);

export const AnalyticsIcon: React.FC<IconProps> = (props) => (
  <Icon {...props}>
    <line x1="18" y1="20" x2="18" y2="10" />
    <line x1="12" y1="20" x2="12" y2="4" />
    <line x1="6" y1="20" x2="6" y2="14" />
  </Icon>
);

// ============================================
// Alert Icons
// ============================================

export const AlertInfoIcon: React.FC<IconProps> = (props) => (
  <Icon {...props} color="default">
    <circle cx="12" cy="12" r="10" />
    <path d="M12 16v-4M12 8h.01" />
  </Icon>
);

export const AlertSuccessIcon: React.FC<IconProps> = (props) => (
  <Icon {...props} color="success">
    <circle cx="12" cy="12" r="10" />
    <path d="M9 12l2 2 4-4" />
  </Icon>
);

export const AlertWarningIcon: React.FC<IconProps> = (props) => (
  <Icon {...props} color="warning">
    <path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
    <path d="M12 9v4M12 17h.01" />
  </Icon>
);

export const AlertErrorIcon: React.FC<IconProps> = (props) => (
  <Icon {...props} color="error">
    <circle cx="12" cy="12" r="10" />
    <path d="M15 9l-6 6M9 9l6 6" />
  </Icon>
);

export const BellIcon: React.FC<IconProps> = (props) => (
  <Icon {...props}>
    <path d="M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9" />
    <path d="M13.73 21a2 2 0 01-3.46 0" />
  </Icon>
);

export const BellRingIcon: React.FC<IconProps> = (props) => (
  <Icon {...props} isAnimated>
    <path d="M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9" />
    <path d="M13.73 21a2 2 0 01-3.46 0" />
    <path d="M6 4a2 2 0 012-2h8a2 2 0 012 2M4 8h16" />
  </Icon>
);

// ============================================
// Signal Icons
// ============================================

export const SignalStrongIcon: React.FC<IconProps> = (props) => (
  <Icon {...props} color="success">
    <path d="M2 20h.01M7 20v-4M12 20v-8M17 20V8M22 20V4" />
  </Icon>
);

export const SignalWeakIcon: React.FC<IconProps> = (props) => (
  <Icon {...props} color="warning">
    <path d="M2 20h.01M7 20v-4M12 20V8" />
    <path d="M17 20V8M22 20V4" strokeOpacity="0.3" />
  </Icon>
);

export const SignalLostIcon: React.FC<IconProps> = (props) => (
  <Icon {...props} color="error">
    <path d="M2 20h.01M7 20v-4M12 20V8" strokeOpacity="0.3" />
    <path d="M17 20V8M22 20V4" strokeOpacity="0.3" />
    <path d="M4 4l16 16" />
  </Icon>
);

export const WifiIcon: React.FC<IconProps> = (props) => (
  <Icon {...props}>
    <path d="M5 12.55a11 11 0 0114.08 0" />
    <path d="M1.42 9a16 16 0 0121.16 0" />
    <path d="M8.53 16.11a6 6 0 016.95 0" />
    <line x1="12" y1="20" x2="12.01" y2="20" />
  </Icon>
);

export default Icon;
