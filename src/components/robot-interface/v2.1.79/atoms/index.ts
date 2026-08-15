/**
 * Atom Components - RaaS UX Kit v2.1.79
 * Basic building blocks for robot interface
 */

export { Button } from './Button';
export type { ButtonProps, ButtonVariant, ButtonSize } from '../types/robot';

export { StatusBadge } from './StatusBadge';
export type { StatusBadgeProps } from '../types/robot';

export { Icon } from './Icon';
export type { IconProps, IconSize, IconColor } from '../types/robot';

// Robot-specific icon exports
export {
  RobotOnlineIcon,
  RobotOfflineIcon,
  RobotChargingIcon,
  RobotBatteryLowIcon,
  RobotErrorIcon,
  RobotWarningIcon,
  PlayIcon,
  PauseIcon,
  StopIcon,
  RestartIcon,
  AbortIcon,
  UploadIcon,
  DownloadIcon,
  SyncIcon,
  RefreshIcon,
  EditIcon,
  DeleteIcon,
  HomeIcon,
  RobotsIcon,
  MissionsIcon,
  SettingsIcon,
  AnalyticsIcon,
  AlertInfoIcon,
  AlertSuccessIcon,
  AlertWarningIcon,
  AlertErrorIcon,
  BellIcon,
  BellRingIcon,
  SignalStrongIcon,
  SignalWeakIcon,
  SignalLostIcon,
  WifiIcon,
} from './Icon';

export { Input, Textarea, Select, Toggle, Slider } from './Input';
export type {
  InputProps,
  InputType,
  InputSize,
  TextareaProps,
  SelectProps,
  SelectOption,
  ToggleProps,
  SliderProps,
} from '../types/robot';
