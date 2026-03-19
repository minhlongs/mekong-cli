# Search Bar

**Version:** 2.1.79 | **Type:** Molecule | **Status:** Stable

---

## Overview

Advanced search component with integrated filtering capabilities for robot fleet management. Combines text input, filter controls, and search history in a unified interface.

---

## Anatomy

```
┌─────────────────────────────────────────────────────────────────┐
│  🔍 [Search input...]                    [Filter ▼]  [Clear ×] │
│  ──────────────────────────────────────────────────────────────  │
│  Recent: /warehouse-A  /charging  low-battery                  │
│  ──────────────────────────────────────────────────────────────  │
│  Filters: [Status: Active ×] [Type: AMR ×] [Zone: A ×]         │
└─────────────────────────────────────────────────────────────────┘
```

### Components

| Element | Atom Reference | Description |
|---------|----------------|-------------|
| Search Input | `text-input` | Primary search field with icon |
| Filter Button | `icon-button` | Opens filter panel |
| Clear Button | `icon-button` | Resets search and filters |
| Filter Chips | `chip` | Active filter display |
| Search History | `text-label` | Recent search patterns |

---

## Variants

### Default
Standard search with filter button.

### With Filters
Displays active filter chips below input.

### With History
Shows recent searches when input is focused.

### Compact
Minimal variant for tight spaces (no history).

---

## States

| State | Description |
|-------|-------------|
| `idle` | Default, ready for input |
| `focused` | Input active, history shown |
| `typing` | User entering text |
| `searching` | Search in progress (loading spinner) |
| `has-results` | Results found, chips displayed |
| `no-results` | Empty state message shown |

---

## Props

```typescript
interface SearchBarProps {
  // Core
  value: string;
  onChange: (value: string) => void;
  onSearch?: (query: string) => void;

  // Filters
  filters?: FilterOption[];
  activeFilters?: FilterOption[];
  onFilterChange?: (filters: FilterOption[]) => void;

  // History
  recentSearches?: string[];
  onRecentSearchClick?: (search: string) => void;

  // Behavior
  placeholder?: string;
  debounceMs?: number;  // Default: 300
  showHistory?: boolean;  // Default: true
  showFilters?: boolean;  // Default: true

  // Styling
  variant?: 'default' | 'compact' | 'minimal';
  className?: string;
}

interface FilterOption {
  id: string;
  label: string;
  category: 'status' | 'type' | 'zone' | 'battery' | 'custom';
  value: string;
}
```

---

## Usage

### Basic Fleet Search

```tsx
<SearchBar
  value={searchQuery}
  onChange={setSearchQuery}
  onSearch={handleFleetSearch}
  placeholder="Search robots by ID, name, or location..."
/>
```

### With Active Filters

```tsx
<SearchBar
  value={query}
  onChange={setQuery}
  filters={[
    { id: 'status-active', label: 'Active', category: 'status', value: 'active' },
    { id: 'type-amr', label: 'AMR', category: 'type', value: 'amr' },
  ]}
  activeFilters={selectedFilters}
  onFilterChange={setSelectedFilters}
  onSearch={handleFilteredSearch}
/>
```

### With Search History

```tsx
<SearchBar
  value={query}
  onChange={setQuery}
  recentSearches={['/warehouse-A', 'low-battery', 'charging']}
  onRecentSearchClick={applyRecentSearch}
  showHistory={true}
/>
```

---

## Patterns

### Pattern Matching

Supports advanced search syntax:

| Syntax | Example | Matches |
|--------|---------|---------|
| `*` wildcard | `AMR-*` | All AMR robots |
| `/` path | `/zone-A/*` | All robots in zone A |
| `type:` filter | `type:agv` | AGV type robots |
| `status:` filter | `status:error` | Robots in error state |
| `battery:<` | `battery:<20` | Low battery robots |

### Filter Chips

- Displayed horizontally below input
- Click `×` to remove individual filter
- "Clear all" appears when 3+ filters active
- Color-coded by category:
  - Status: Blue
  - Type: Green
  - Zone: Purple
  - Battery: Amber

### Recent Searches

- Maximum 5 items stored
- Click to reapply search
- Dismiss with `×` per item
- Cleared after 24h or manual clear

---

## Accessibility

```html
<!-- ARIA Structure -->
<div role="search" aria-label="Fleet search">
  <input
    type="text"
    role="searchbox"
    aria-label="Search robots"
    aria-controls="search-results"
    aria-expanded="{isFocused}"
    aria-autocomplete="list"
  />
  <div role="listbox" id="search-history">
    <option role="option">Recent search 1</option>
  </div>
</div>
```

**Keyboard Navigation:**

| Key | Action |
|-----|--------|
| `Enter` | Execute search |
| `Escape` | Close history, clear input |
| `↑/↓` | Navigate history/results |
| `Tab` | Move to filter button |

---

## Responsive Behavior

| Breakpoint | Behavior |
|------------|----------|
| `sm` (<640px) | Full width, filters in drawer |
| `md` (640-1024px) | Inline filters, condensed history |
| `lg` (>1024px) | Full features, expanded view |

---

## Related Components

- **Organisms:** `FilterPanel`, `SearchResults`
- **Atoms:** `TextInput`, `IconButton`, `Chip`, `TextLabel`

---

## Changelog

| Version | Date | Change |
|---------|------|--------|
| 2.1.79 | 2026-03-19 | Initial molecule documentation |
