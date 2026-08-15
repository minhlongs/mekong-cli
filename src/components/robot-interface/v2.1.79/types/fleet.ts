/**
 * Fleet Types - RaaS UX Kit v2.1.79
 * Fleet management and search types
 */

// ============================================
// Search Bar Types
// ============================================

export type SearchCategory = 'status' | 'type' | 'zone' | 'battery' | 'custom';

export type SearchVariant = 'default' | 'compact' | 'minimal';

export interface SearchFilter {
  id: string;
  label: string;
  category: SearchCategory;
  value: string;
  icon?: React.ReactNode;
}

export interface FilterChip {
  id: string;
  label: string;
  category: SearchCategory;
  onRemove: () => void;
}

export interface SearchBarProps {
  // Core
  value?: string;
  onChange: (value: string) => void;
  onSearch?: (query: string) => void;

  // Filters
  filters?: SearchFilter[];
  activeFilters?: string[]; // Array of filter IDs
  onFilterToggle?: (filterId: string) => void;

  // History
  recentSearches?: string[];
  onRecentSearchSelect?: (search: string) => void;
  onRecentSearchClear?: () => void;

  // Behavior
  placeholder?: string;
  debounceMs?: number;
  showHistory?: boolean;
  showFilters?: boolean;

  // Styling
  variant?: SearchVariant;
  className?: string;
  disabled?: boolean;

  // Actions
  onClear?: () => void;
}

// ============================================
// Fleet Types
// ============================================

export type FleetStatus = 'all' | 'online' | 'offline' | 'charging' | 'error' | 'warning' | 'busy' | 'idle' | 'paused' | 'maintenance';

export type FleetViewMode = 'grid' | 'list' | 'map';

export type FleetSortField = 'name' | 'status' | 'battery' | 'lastActive' | 'location';

export type FleetSortOrder = 'asc' | 'desc';

export interface FleetFilter {
  statuses: FleetStatus[];
  zone?: string;
  batteryMin?: number;
  searchQuery?: string;
}

export interface FleetSort {
  field: FleetSortField;
  order: FleetSortOrder;
}

export interface FleetPagination {
  page: number;
  pageSize: number;
  total: number;
}

export interface FleetState {
  filters: FleetFilter;
  sort: FleetSort;
  pagination: FleetPagination;
  viewMode: FleetViewMode;
}

// ============================================
// Fleet Card Props
// ============================================

export interface FleetCardProps {
  robotId: string;
  robotName: string;
  status: import('./robot').RobotStatus;
  batteryLevel: number;
  signalStrength: number;
  location?: string;
  currentMission?: string;
  lastActive?: Date;
  onClick?: () => void;
  isSelected?: boolean;
}

// ============================================
// Fleet Grid Props
// ============================================

export interface FleetGridProps {
  robots: import('./robot').Robot[];
  selectedRobotId?: string;
  onRobotSelect?: (robotId: string) => void;
  viewMode?: FleetViewMode;
  isLoading?: boolean;
  className?: string;
}
