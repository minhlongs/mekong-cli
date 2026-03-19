/**
 * Robot Interface Types
 * RaaS UX Kit v2.1.79
 */

// ============================================
// Robot Status Types
// ============================================

export type RobotConnectionState = 'online' | 'offline' | 'reconnecting' | 'unknown';

export type RobotMode = 'auto' | 'manual' | 'teleop' | 'charging' | 'sleep' | 'error';

export type RobotStatus = 'online' | 'offline' | 'charging' | 'error' | 'warning' | 'busy' | 'idle' | 'paused' | 'maintenance';

export type BatteryHealth = 'good' | 'fair' | 'poor';

export type SignalType = 'wifi' | 'cellular' | 'ethernet';

export type SignalQuality = 'excellent' | 'good' | 'fair' | 'poor';

export type TemperatureState = 'cold' | 'normal' | 'warm' | 'hot' | 'critical';

// ============================================
// Robot Core Interfaces
// ============================================

export interface Robot {
  id: string;
  name: string;
  serialNumber?: string;
  type: RobotType;
  status: RobotStatus;
  mode: RobotMode;
  connectionState: RobotConnectionState;
  location: RobotLocation;
  battery: BatteryStatus;
  signal: SignalStatus;
  temperature: TemperatureStatus;
  lastSeen?: Date;
  createdAt: Date;
  updatedAt: Date;
}

export interface RobotType {
  id: string;
  name: string;
  category: 'AMR' | 'AGV' | 'Arm' | 'Humanoid' | 'Custom';
  maxSpeed: number; // mm/s
  maxPayload: number; // kg
  dimensions: RobotDimensions;
}

export interface RobotDimensions {
  length: number; // mm
  width: number; // mm
  height: number; // mm
  weight: number; // kg
}

export interface RobotLocation {
  zone?: string;
  x?: number; // mm
  y?: number; // mm
  z?: number; // mm
  heading?: number; // degrees
}

// ============================================
// Battery Types
// ============================================

export interface BatteryStatus {
  level: number; // 0-100
  charging: boolean;
  health: BatteryHealth;
  voltage?: number; // V
  current?: number; // A
  temperature?: number; // °C
  estimatedRuntime?: number; // minutes
  estimatedChargeTime?: number; // minutes
  cycles?: number; // charge cycles
}

// ============================================
// Signal Types
// ============================================

export interface SignalStatus {
  strength: number; // dBm (-100 to -30)
  type: SignalType;
  quality: SignalQuality;
  ssid?: string;
  bssid?: string;
  ip?: string;
  mac?: string;
}

// ============================================
// Temperature Types
// ============================================

export interface TemperatureStatus {
  current: number; // °C
  max: number; // °C
  min?: number; // °C
  state: TemperatureState;
  zones?: TemperatureZone[];
}

export interface TemperatureZone {
  name: string;
  temperature: number; // °C
  state: TemperatureState;
}

// ============================================
// Status Badge Types
// ============================================

export interface StatusBadgeProps {
  variant: RobotStatus;
  size?: 'sm' | 'md' | 'lg';
  isPulsing?: boolean;
  isDropdown?: boolean;
  onClick?: () => void;
  children: React.ReactNode;
  className?: string;
}

// ============================================
// Button Types
// ============================================

export type ButtonVariant = 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger' | 'emergency-stop';

export type ButtonSize = 'sm' | 'md' | 'lg' | 'xl';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  isLoading?: boolean;
  isDisabled?: boolean;
  icon?: React.ReactNode;
  confirmRequired?: boolean;
  confirmMessage?: string;
  children?: React.ReactNode;
  className?: string;
}

// ============================================
// Badge Types
// ============================================

export type BadgeVariant = 'default' | 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'info';

export type BadgeSize = 'sm' | 'md' | 'lg';

export interface BadgeProps {
  variant?: BadgeVariant;
  size?: BadgeSize;
  children: React.ReactNode;
  className?: string;
}

// ============================================
// Icon Types
// ============================================

export type IconSize = 'xs' | 'sm' | 'md' | 'lg' | 'xl' | '2xl';

export type IconColor = 'default' | 'secondary' | 'success' | 'warning' | 'error' | 'critical';

export interface IconProps extends React.SVGProps<SVGSVGElement> {
  size?: IconSize;
  color?: IconColor;
  isAnimated?: boolean;
  className?: string;
}

// ============================================
// Input Types
// ============================================

export type InputType = 'text' | 'email' | 'number' | 'password' | 'tel' | 'url';

export type InputSize = 'sm' | 'md' | 'lg';

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  type?: InputType;
  size?: InputSize;
  label?: string;
  error?: string;
  helperText?: string;
  prefix?: React.ReactNode;
  suffix?: React.ReactNode;
  clearable?: boolean;
  onClear?: () => void;
  className?: string;
}

export interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string;
  helperText?: string;
  rows?: number;
  maxRows?: number;
  autoResize?: boolean;
  className?: string;
}

export interface SelectOption {
  value: string;
  label: string;
  icon?: React.ReactNode;
  disabled?: boolean;
}

export interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  error?: string;
  helperText?: string;
  options: SelectOption[];
  placeholder?: string;
  searchable?: boolean;
  multi?: boolean;
  className?: string;
}

export interface ToggleProps {
  checked: boolean;
  onChange: (checked: boolean) => void;
  label?: string;
  size?: 'sm' | 'md' | 'lg';
  disabled?: boolean;
  labels?: { on: string; off: string };
  variant?: 'default' | 'success' | 'danger';
  confirmRequired?: boolean;
  confirmMessage?: string;
  className?: string;
}

export interface SliderProps {
  value: number;
  onChange: (value: number) => void;
  min?: number;
  max?: number;
  step?: number;
  label?: string;
  unit?: string;
  marks?: number[];
  renderMark?: (value: number) => React.ReactNode;
  warningThreshold?: number;
  range?: boolean;
  disabled?: boolean;
  className?: string;
}

// ============================================
// Common Utility Types
// ============================================

export interface TimeRange {
  label: string;
  value: string;
  duration: number; // milliseconds
}

export interface Point {
  x: number;
  y: number;
}

export interface Dimensions {
  width: number;
  height: number;
}

export interface Position {
  top?: number;
  right?: number;
  bottom?: number;
  left?: number;
}

// ============================================
// Theme Types
// ============================================

export type Theme = 'light' | 'dark' | 'system';

export interface ThemeContextType {
  theme: Theme;
  actualTheme: 'light' | 'dark';
  setTheme: (theme: Theme) => void;
  toggleTheme: () => void;
}

// ============================================
// Event Types
// ============================================

export interface RobotEvent {
  id: string;
  robotId: string;
  type: EventType;
  level: EventLevel;
  message: string;
  data?: Record<string, unknown>;
  timestamp: Date;
  acknowledged?: boolean;
  acknowledgedAt?: Date;
  acknowledgedBy?: string;
}

export type EventType = 'status_change' | 'mode_change' | 'battery_low' | 'error' | 'warning' | 'mission_start' | 'mission_complete' | 'connection_lost' | 'connection_restored';

export type EventLevel = 'debug' | 'info' | 'warn' | 'error' | 'critical';

// ============================================
// Control Panel Types
// ============================================

export interface ControlPanelProps {
  robotStatus?: RobotStatus;
  isPlaying?: boolean;
  isPaused?: boolean;
  isLoading?: boolean;
  emergencyArmed?: boolean;
  onPlay?: () => void;
  onPause?: () => void;
  onStop?: () => void;
  onEmergencyStop?: () => void;
  onRestart?: () => void;
  disabled?: boolean;
  className?: string;
}

// ============================================
// Notification Types
// ============================================

export type NotificationType = 'info' | 'success' | 'warning' | 'error' | 'critical';

export type NotificationPosition = 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left' | 'top-center' | 'bottom-center';

export type NotificationSize = 'sm' | 'md' | 'lg';

export interface NotificationAction {
  label: string;
  onClick: () => void;
  variant?: 'primary' | 'secondary' | 'danger';
}

export interface NotificationProps {
  id: string;
  type?: NotificationType;
  title?: string;
  message: string;
  action?: NotificationAction;
  onDismiss?: () => void;
  duration?: number; // ms, 0 = no auto-dismiss
  position?: NotificationPosition;
  size?: NotificationSize;
  showProgress?: boolean;
  className?: string;
}

export interface NotificationState {
  notifications: Array<{
    id: string;
    type: NotificationType;
    title?: string;
    message: string;
    action?: NotificationAction;
    createdAt: number;
    duration?: number;
  }>;
  addNotification: (notification: Omit<NotificationProps, 'id'>) => string;
  removeNotification: (id: string) => void;
  clearAll: () => void;
}
