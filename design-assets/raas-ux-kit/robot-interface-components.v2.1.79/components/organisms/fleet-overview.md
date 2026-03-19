# Fleet Overview

**Version:** 2.1.79 | **Type:** Organism | **Status:** Production Ready

---

## Overview

Multi-robot fleet management interface providing grid and list views, filtering, sorting, and bulk operations for managing robot fleets at scale.

---

## Anatomy

### Grid View

```
┌─────────────────────────────────────────────────────────────────────┐
│  FLEET OVERVIEW                    [Grid] [List]  [+ Add Robot]     │
│  24 robots  |  18 online  |  4 in mission  |  2 maintenance         │
├─────────────────────────────────────────────────────────────────────┤
│  Filters:  [Status ▼]  [Mode ▼]  [Location ▼]  [Search...]         │
├─────────────────────────────────────────────────────────────────────┤
│  ┌───────────────┐ ┌───────────────┐ ┌───────────────┐             │
│  │ ROBOT-001     │ │ ROBOT-002     │ │ ROBOT-003     │             │
│  │ Warehouse A   │ │ Warehouse A   │ │ Warehouse B   │             │
│  │ ━━━━━━━━━━━━  │ │ ━━━━━━━━━━━━  │ │ ━━━━━━━━━━━━  │             │
│  │ ● Online      │ │ ● Online      │ │ ○ Offline     │             │
│  │ ▓▓▓▓▓░ 82%    │ │ ▓▓▓░░░ 61%    │ │ ▓▓▓▓▓▓ 100%   │             │
│  │ [AUTO]        │ │ [MANUAL]      │ │ [CHARGING]    │             │
│  │ [Select ✓]    │ │ [Select ✓]    │ │ [Select ✓]    │             │
│  └───────────────┘ └───────────────┘ └───────────────┘             │
│  ┌───────────────┐ ┌───────────────┐ ┌───────────────┐             │
│  │ ROBOT-004     │ │ ROBOT-005     │ │ ROBOT-006     │             │
│  │ ...           │ │ ...           │ │ ...           │             │
│  └───────────────┘ └───────────────┘ └───────────────┘             │
├─────────────────────────────────────────────────────────────────────┤
│  [ ] Select All (8)    [Start Mission] [Charge] [Locate] [Stop]    │
└─────────────────────────────────────────────────────────────────────┘
```

### List View

```
┌─────────────────────────────────────────────────────────────────────┐
│  FLEET OVERVIEW                    [Grid] [List]  [+ Add Robot]     │
├─────────────────────────────────────────────────────────────────────┤
│  [☐] Name           │ Location    │ Status  │ Battery │ Mode  │ ... │
├─────────────────────────────────────────────────────────────────────┤
│  [✓] ROBOT-001      │ Warehouse A │ ● Onln  │ ▓▓▓▓ 82%│ AUTO  │ ⋮   │
│  [✓] ROBOT-002      │ Warehouse A │ ● Onln  │ ▓▓▓░ 61%│ MAN   │ ⋮   │
│  [ ] ROBOT-003      │ Warehouse B │ ○ Off   │ ▓▓▓▓100%│ CHG   │ ⋮   │
│  [✓] ROBOT-004      │ Warehouse B │ ● Onln  │ ▓▓░░ 45%│ AUTO  │ ⋮   │
│  [ ] ROBOT-005      │ Warehouse C │ ⚠ Maint │ ▓▓▓▓ 95%│ OFF   │ ⋮   │
├─────────────────────────────────────────────────────────────────────┤
│  4 selected    [Start Mission] [Charge] [Locate] [Stop ⚠️]          │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Props Interface

```typescript
interface FleetOverviewProps {
  // Data
  robots: Robot[];
  isLoading?: boolean;

  // View
  viewMode: 'grid' | 'list';
  onViewModeChange: (mode: 'grid' | 'list') => void;

  // Filtering
  filters: FleetFilters;
  onFilterChange: (filters: FleetFilters) => void;

  // Sorting
  sortConfig: SortConfig;
  onSortChange: (config: SortConfig) => void;

  // Selection
  selectedRobotIds: string[];
  onSelectionChange: (ids: string[]) => void;

  // Bulk Actions
  onBulkStartMission?: (robotIds: string[]) => void;
  onBulkCharge?: (robotIds: string[]) => void;
  onBulkLocate?: (robotIds: string[]) => void;
  onBulkStop?: (robotIds: string[]) => void;
  onBulkReboot?: (robotIds: string[]) => void;

  // Row/Card Actions
  onRobotClick: (robotId: string) => void;
  onQuickAction?: (robotId: string, action: string) => void;

  // Pagination
  pagination?: PaginationConfig;
  onPageChange?: (page: number) => void;

  // Styling
  className?: string;
  compact?: boolean;
}

interface FleetFilters {
  status?: RobotStatus[];
  mode?: RobotMode[];
  location?: string[];
  batteryRange?: { min: number; max: number };
  search?: string;
}

interface SortConfig {
  field: string;
  direction: 'asc' | 'desc';
}
```

---

## View Modes

### Grid View

```tsx
<FleetGrid
  robots={filteredRobots}
  columns={gridColumns}
  cardComponent={RobotStatusCard}
  onSelect={handleCardSelect}
  selectedIds={selectedRobotIds}
  onQuickAction={handleQuickAction}
/>
```

### List View

```tsx
<FleetList
  robots={filteredRobots}
  columns={listColumns}
  sortable={true}
  sortConfig={sortConfig}
  onSort={handleSort}
  onSelect={handleRowSelect}
  selectedIds={selectedRobotIds}
  onRowClick={handleRowClick}
/>
```

---

## Filtering System

### Filter Options

```typescript
const STATUS_OPTIONS = [
  { value: 'online', label: 'Online', count: 18 },
  { value: 'offline', label: 'Offline', count: 4 },
  { value: 'reconnecting', label: 'Reconnecting', count: 2 },
  { value: 'maintenance', label: 'Maintenance', count: 2 },
];

const MODE_OPTIONS = [
  { value: 'auto', label: 'Auto', icon: <AutoIcon />, count: 12 },
  { value: 'manual', label: 'Manual', icon: <ManualIcon />, count: 6 },
  { value: 'charging', label: 'Charging', icon: <ChargingIcon />, count: 4 },
  { value: 'sleep', label: 'Sleep', icon: <SleepIcon />, count: 2 },
  { value: 'error', label: 'Error', icon: <ErrorIcon />, count: 2 },
];

const LOCATION_OPTIONS = [
  { value: 'warehouse-a', label: 'Warehouse A', count: 10 },
  { value: 'warehouse-b', label: 'Warehouse B', count: 8 },
  { value: 'warehouse-c', label: 'Warehouse C', count: 6 },
];
```

### Filter UI

```tsx
<FleetFilters
  filters={filters}
  onFilterChange={setFilters}
>
  {/* Status Multi-Select */}
  <FilterGroup label="Status" icon={<StatusIcon />}>
    <MultiSelect
      options={STATUS_OPTIONS}
      value={filters.status}
      onChange={(values) => setFilters({ ...filters, status: values })}
      renderOption={(option) => (
        <FilterOptionWithCount
          dot={getStatusColor(option.value)}
          label={option.label}
          count={option.count}
        />
      )}
    />
  </FilterGroup>

  {/* Mode Multi-Select */}
  <FilterGroup label="Mode" icon={<ModeIcon />}>
    <MultiSelect
      options={MODE_OPTIONS}
      value={filters.mode}
      onChange={(values) => setFilters({ ...filters, mode: values })}
    />
  </FilterGroup>

  {/* Location Multi-Select */}
  <FilterGroup label="Location" icon={<LocationIcon />}>
    <MultiSelect
      options={LOCATION_OPTIONS}
      value={filters.location}
      onChange={(values) => setFilters({ ...filters, location: values })}
    />
  </FilterGroup>

  {/* Battery Range Slider */}
  <FilterGroup label="Battery" icon={<BatteryIcon />}>
    <RangeSlider
      min={0}
      max={100}
      value={filters.batteryRange}
      onChange={(range) => setFilters({ ...filters, batteryRange: range })}
      renderLabel={(value) => `${value}%`}
    />
  </FilterGroup>

  {/* Search */}
  <SearchInput
    placeholder="Search by ID, name, or serial..."
    value={filters.search}
    onChange={(search) => setFilters({ ...filters, search })}
  />
</FleetFilters>
```

---

## Sorting System

### Sortable Columns (List View)

```typescript
const SORTABLE_COLUMNS = [
  { field: 'name', label: 'Name', defaultDirection: 'asc' },
  { field: 'location', label: 'Location', defaultDirection: 'asc' },
  { field: 'status', label: 'Status', defaultDirection: 'desc' },
  { field: 'battery.level', label: 'Battery', defaultDirection: 'desc' },
  { field: 'mode', label: 'Mode', defaultDirection: 'asc' },
  { field: 'lastSeen', label: 'Last Seen', defaultDirection: 'desc' },
  { field: 'missionProgress', label: 'Progress', defaultDirection: 'desc' },
];
```

### Sort Handler

```tsx
<FleetList
  robots={robots}
  sortConfig={sortConfig}
  onSort={(field) => {
    const direction =
      sortConfig.field === field && sortConfig.direction === 'asc'
        ? 'desc'
        : 'asc';
    setSortConfig({ field, direction });
  }}
>
  {SORTABLE_COLUMNS.map((col) => (
    <SortableHeader
      key={col.field}
      field={col.field}
      active={sortConfig.field === col.field}
      direction={sortConfig.direction}
    >
      {col.label}
    </SortableHeader>
  ))}
</FleetList>
```

---

## Selection & Bulk Actions

### Selection Bar

```tsx
<SelectionBar
  selectedCount={selectedRobotIds.length}
  totalCount={robots.length}
  onSelectAll={(checked) => {
    if (checked) {
      setSelectedRobotIds(filteredRobots.map(r => r.id));
    } else {
      setSelectedRobotIds([]);
    }
  }}
  actions={[
    {
      key: 'start-mission',
      label: 'Start Mission',
      icon: <PlayIcon />,
      onClick: () => onBulkStartMission?.(selectedRobotIds),
      requiresSelection: true,
    },
    {
      key: 'charge',
      label: 'Return to Charge',
      icon: <BatteryIcon />,
      onClick: () => onBulkCharge?.(selectedRobotIds),
      requiresSelection: true,
    },
    {
      key: 'locate',
      label: 'Locate',
      icon: <TargetIcon />,
      onClick: () => onBulkLocate?.(selectedRobotIds),
      requiresSelection: true,
    },
    {
      key: 'stop',
      label: 'Emergency Stop',
      icon: <StopIcon />,
      variant: 'danger',
      onClick: handleBulkStop,
      requiresSelection: true,
      requiresConfirmation: true,
    },
  ]}
/>
```

### Bulk Action Handlers

```typescript
// Optimistic for reversible actions
const handleBulkLocate = async (robotIds: string[]) => {
  // 1. Show loading state on selected robots
  setRobotStates(prev =>
    prev.map(r =>
      robotIds.includes(r.id) ? { ...r, locating: true } : r
    )
  );

  try {
    // 2. Send parallel requests
    await Promise.all(
      robotIds.map(id => api.locateRobot(id))
    );

    // 3. Success feedback
    toast.success(`Locating ${robotIds.length} robots`);

    // 4. Clear loading state
    setRobotStates(prev =>
      prev.map(r => ({ ...r, locating: false }))
    );
  } catch (error) {
    toast.error(`Failed to locate some robots`);
  }
};

// Pessimistic for destructive actions
const handleBulkStop = async () => {
  // 1. Confirmation required
  const confirmed = await confirmAction({
    title: 'Emergency Stop All Selected?',
    message: `This will immediately stop ${selectedRobotIds.length} robots.`,
    variant: 'danger',
    confirmText: 'STOP ALL',
  });

  if (!confirmed) return;

  // 2. Wait for all to confirm stopped
  setIsStoppingAll(true);
  try {
    await Promise.all(
      selectedRobotIds.map(id => api.emergencyStop(id))
    );
    toast.warning(`Stopped ${selectedRobotIds.length} robots`);
  } finally {
    setIsStoppingAll(false);
  }
};
```

---

## Real-Time Data Handling

### Fleet-Wide Updates

```typescript
// WebSocket subscription for fleet updates
useFleetWebSocket({
  onRobotUpdate: (robotId: string, update: RobotUpdate) => {
    // Optimistic: Update individual robot immediately
    setRobots(prev =>
      prev.map(r =>
        r.id === robotId ? { ...r, ...update } : r
      )
    );
  },

  onRobotAdded: (robot: Robot) => {
    // Optimistic: Add to list
    setRobots(prev => [...prev, robot]);
  },

  onRobotRemoved: (robotId: string) => {
    // Pessimistic: Verify before removing
    if (robots.find(r => r.id === robotId)) {
      setRobots(prev => prev.filter(r => r.id !== robotId));
    }
  },

  onBulkStatusChange: (updates: { id: string; status: string }[]) => {
    // Batch update for efficiency
    setRobots(prev =>
      prev.map(r => {
        const update = updates.find(u => u.id === r.id);
        return update ? { ...r, status: update.status } : r;
      })
    );
  },
});
```

### Optimistic UI Patterns

```typescript
// Battery updates - optimistic (non-critical)
const handleBatteryUpdate = (robotId: string, level: number) => {
  setRobots(prev =>
    prev.map(r =>
      r.id === robotId
        ? { ...r, battery: { ...r.battery, level } }
        : r
    )
  );
};

// Mode changes - optimistic for user actions
const handleModeChange = async (robotId: string, newMode: string) => {
  // 1. Optimistic update
  setRobots(prev =>
    prev.map(r =>
      r.id === robotId ? { ...r, mode: newMode } : r
    )
  );

  try {
    // 2. Server sync
    await api.updateMode(robotId, newMode);
  } catch {
    // 3. Rollback
    setRobots(prev =>
      prev.map(r =>
        r.id === robotId ? { ...r, mode: r.previousMode } : r
      )
    );
  }
};

// Status changes - pessimistic (server-authoritative)
const handleStatusChange = (robotId: string, newStatus: string) => {
  // Wait for server push, never guess status
  refreshRobotStatus(robotId);
};
```

---

## Offline State Management

### Offline Behavior

```tsx
const OfflineFleetOverview = () => {
  const { isOffline, lastSync, cachedRobots } = useFleetContext();

  return (
    <Panel>
      {isOffline && (
        <OfflineBanner>
          <WifiOffIcon />
          <span>
            Offline. Showing cached state from {formatDistance(lastSync)}.
            Bulk actions disabled.
          </span>
        </OfflineBanner>
      )}

      <FleetGrid
        robots={cachedRobots}
        // Selection still works offline
        selectedIds={selectedRobotIds}
        onSelect={setSelectedRobotIds}

        {/* Disable interactive actions */}
        actionsDisabled={isOffline}

        {/* Visual indicator for stale data */}
        cardProps={{
          faded: isOffline,
          showStaleBadge: true,
          staleSince: lastSync,
        }}
      />

      {/* Bulk actions disabled */}
      <SelectionBar
        actions={BULK_ACTIONS.map(a => ({
          ...a,
          disabled: isOffline || a.disabled,
        }))}
      />
    </Panel>
  );
};
```

### Cache Strategy

```typescript
// Multi-layer caching for fleet data
const fleetCacheConfig = {
  // L1: In-memory (current session)
  memory: {
    maxRobots: 500,
    ttl: 60000, // 1 minute
  },

  // L2: IndexedDB (persistent)
  indexedDB: {
    maxAge: 24 * 60 * 60 * 1000, // 24 hours
    syncOnReconnect: true,
  },

  // Background refresh
  backgroundRefresh: {
    interval: 30000, // 30 seconds
    staggerRequests: true,
    batchSize: 10,
  },
};
```

---

## Emergency Stop Integration

### Bulk E-Stop Placement

```
┌─────────────────────────────────────────────────────────┐
│  FLEET OVERVIEW                    [Grid] [List]  [+]   │
│                                                         │
│  [Filters Row]                                          │
│                                                         │
│  [Grid/List Content]                                    │
│                                                         │
│  ─────────────────────────────────────────────────────  │
│  [ ] All  │  8 selected  │  [...]  │  [🔴 E-STOP ALL]  │  ← Fixed bottom
└─────────────────────────────────────────────────────────┘
```

### Styling

```scss
.bulk-emergency-stop {
  position: sticky;
  bottom: 0;
  z-index: 100;

  background: $red-600;
  color: white;
  padding: 0.75rem 1.5rem;

  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;

  border-top: 3px solid $red-800;
  box-shadow: 0 -4px 12px rgba(220, 38, 38, 0.3);

  // Disabled when no selection
  &:disabled {
    background: $gray-400;
    border-top-color: $gray-500;
    box-shadow: none;
    cursor: not-allowed;
  }

  &:not(:disabled):hover {
    background: $red-700;
    box-shadow: 0 -6px 16px rgba(220, 38, 38, 0.4);
  }

  // Pulse when selection > threshold
  &[data-count-gte="10"] {
    animation: pulse-bulk-stop 1.5s infinite;
  }
}
```

### Confirmation Flow

```tsx
const BulkEmergencyStopDialog = ({
  robotCount,
  robots,
  onConfirm,
  onCancel,
}) => (
  <Dialog open variant="danger" size="lg">
    <DialogHeader>
      <AlertTriangleIcon className="text-red-600 w-16 h-16" />
      <DialogTitle>
        Emergency Stop {robotCount} Robots?
      </DialogTitle>
    </DialogHeader>

    <DialogContent>
      <p className="text-lg font-semibold mb-4">
        This action will immediately halt all selected robots.
      </p>

      <Alert variant="warning" className="mb-4">
        <ul className="list-disc pl-4 space-y-1">
          <li>All active missions will be aborted</li>
          <li>Robots will engage emergency brakes</li>
          <li>Systems will enter safe mode</li>
          <li>Manual restart required for each robot</li>
        </ul>
      </Alert>

      {/* Preview of affected robots */}
      <div className="max-h-60 overflow-auto border rounded p-2">
        <p className="text-sm font-medium mb-2">
          Affected Robots ({robotCount}):
        </p>
        <ul className="text-sm space-y-1">
          {robots.slice(0, 10).map(r => (
            <li key={r.id} className="flex justify-between">
              <span>{r.name}</span>
              <span className="text-gray-500">{r.location}</span>
            </li>
          ))}
          {robots.length > 10 && (
            <li className="text-gray-500 italic">
              +{robots.length - 10} more...
            </li>
          )}
        </ul>
      </div>
    </DialogContent>

    <DialogFooter>
      <Button variant="ghost" onClick={onCancel}>
        Cancel
      </Button>
      <Button
        variant="danger"
        onClick={onConfirm}
        className="min-w-[160px]"
      >
        🛑 STOP {robotCount} ROBOTS
      </Button>
    </DialogFooter>
  </Dialog>
);
```

---

## Stat Cards (Header Summary)

```tsx
<FleetStatsBar robots={robots}>
  <StatCard
    label="Total Robots"
    value={robots.length}
    icon={<RobotIcon />}
  />
  <StatCard
    label="Online"
    value={onlineCount}
    icon={<OnlineIcon />}
    color="green"
    trend={onlineTrend}
  />
  <StatCard
    label="In Mission"
    value={missionCount}
    icon={<MissionIcon />}
    color="blue"
  />
  <StatCard
    label="Maintenance"
    value={maintenanceCount}
    icon={<MaintenanceIcon />}
    color="amber"
  />
  <StatCard
    label="Offline"
    value={offlineCount}
    icon={<OfflineIcon />}
    color="red"
    alert={offlineCount > threshold}
  />
</FleetStatsBar>
```

---

## Usage Examples

### Full Fleet Management

```tsx
<FleetOverview
  robots={allRobots}
  viewMode={viewMode}
  onViewModeChange={setViewMode}
  filters={filters}
  onFilterChange={setFilters}
  sortConfig={sortConfig}
  onSortChange={setSortConfig}
  selectedRobotIds={selectedRobotIds}
  onSelectionChange={setSelectedRobotIds}
  onBulkStartMission={handleBulkMission}
  onBulkCharge={handleBulkCharge}
  onBulkLocate={handleBulkLocate}
  onBulkStop={handleBulkStop}
  onRobotClick={(id) => navigate(`/robots/${id}`)}
  onQuickAction={handleQuickAction}
  pagination={{
    page: currentPage,
    pageSize: 24,
    total: allRobots.length,
  }}
  onPageChange={setCurrentPage}
/>
```

### Read-Only Dashboard Widget

```tsx
<FleetOverview
  robots={filteredRobots}
  viewMode="grid"
  filters={dashboardFilters}
  onRobotClick={(id) => navigate(`/robots/${id}`)}
  // Disable interactive features
  onSelectionChange={undefined}
  onBulkStartMission={undefined}
/>
```

---

## Related Components

- **Robot Status Panel** - Individual robot detail
- **Mission Control** - Single-robot mission management
- **Telemetry Dashboard** - Robot telemetry visualization

---

## Changelog

| Version | Date | Change |
|---------|------|--------|
| 2.1.79 | 2026-03-19 | Initial organism documentation |
| 2.1.78 | 2026-03-15 | Added bulk selection with staggered updates |
| 2.1.77 | 2026-03-10 | Multi-location filter support |
