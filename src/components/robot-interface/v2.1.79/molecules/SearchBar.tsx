/**
 * SearchBar Component - RaaS UX Kit v2.1.79
 * Fleet search with integrated filtering and pattern matching
 */
import React, { useState, useCallback, useRef, useEffect } from 'react';
import { SearchBarProps } from '../types/fleet';
import { Input } from '../atoms/Input';
import { Button } from '../atoms/Button';

export const SearchBar: React.FC<SearchBarProps> = ({
  value = '',
  onChange,
  filters = [],
  activeFilters = [],
  recentSearches = [],
  onFilterToggle,
  onClear,
  onSearch,
  onRecentSearchSelect,
  onRecentSearchClear,
  placeholder = 'Search robots, missions, locations...',
  className = '',
  disabled = false,
}) => {
  const [showHistory, setShowHistory] = useState(false);
  const [showFilters, setShowFilters] = useState(false);
  const searchBarRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (searchBarRef.current && !searchBarRef.current.contains(event.target as Node)) {
        setShowHistory(false);
        setShowFilters(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => onChange?.(e.target.value), [onChange]);
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLInputElement>) => {
      if (e.key === 'Enter' && value.trim()) {
        onSearch?.(value.trim());
        setShowHistory(false);
      }
    },
    [value, onSearch]
  );

  return (
    <div ref={searchBarRef} className={`flex flex-col gap-2 ${className}`}>
      <div className="flex items-center gap-2">
        <div className="flex-1 relative">
          <Input
            type="text"
            size="md"
            value={value}
            onChange={handleChange}
            onKeyDown={handleKeyDown}
            onFocus={() => recentSearches.length > 0 && setShowHistory(true)}
            placeholder={placeholder}
            disabled={disabled}
            clearable={value.length > 0}
            onClear={() => { onClear?.(); setShowHistory(false); }}
            prefix={
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                <circle cx="11" cy="11" r="8" strokeWidth="2" /><path d="M21 21l-4.35-4.35" strokeWidth="2" />
              </svg>
            }
            suffix={
              <Button variant="ghost" size="sm" onClick={() => setShowFilters(!showFilters)} className="p-1" aria-label="Toggle filters">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                  <path d="M3 4h18M3 12h12M3 20h6" strokeWidth="2" />
                </svg>
              </Button>
            }
          />

          {showHistory && recentSearches.length > 0 && (
            <div className="absolute top-full left-0 right-0 mt-1 bg-[var(--color-surface)] border border-[var(--color-border)] rounded-[var(--radius-md)] shadow-lg z-50 max-h-60 overflow-auto">
              <div className="p-2 border-b border-[var(--color-border)] flex items-center justify-between">
                <span className="text-xs font-medium text-[var(--color-text-secondary)]">Recent Searches</span>
                <button type="button" onClick={onRecentSearchClear} className="text-xs text-[var(--color-text-tertiary)] hover:text-[var(--color-text-secondary)] cursor-pointer">
                  Clear all
                </button>
              </div>
              <div className="py-1">
                {recentSearches.map((search, index) => (
                  <button
                    key={index}
                    type="button"
                    className="w-full px-3 py-2 text-left flex items-center gap-2 hover:bg-[var(--color-surface-tertiary)] cursor-pointer"
                    onClick={() => { onRecentSearchSelect?.(search); setShowHistory(false); }}
                  >
                    <svg className="w-3.5 h-3.5 text-[var(--color-text-tertiary)]" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                      <path d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" strokeWidth="2" />
                    </svg>
                    <span className="text-sm text-[var(--color-text-primary)]">{search}</span>
                  </button>
                ))}
              </div>
            </div>
          )}

          {showFilters && (
            <div className="absolute top-full left-0 mt-1 bg-[var(--color-surface)] border border-[var(--color-border)] rounded-[var(--radius-md)] shadow-lg z-50 min-w-[200px]">
              <div className="p-2 border-b border-[var(--color-border)]">
                <span className="text-xs font-medium text-[var(--color-text-secondary)]">Filters</span>
              </div>
              <div className="py-1">
                {filters.map((filter) => {
                  const isActive = activeFilters.includes(filter.id);
                  return (
                    <button
                      key={filter.id}
                      type="button"
                      className={`w-full px-3 py-2 text-left flex items-center justify-between hover:bg-[var(--color-surface-tertiary)] cursor-pointer ${
                        isActive ? 'bg-[var(--color-primary-container)]' : ''
                      }`}
                      onClick={() => onFilterToggle?.(filter.id)}
                    >
                      <span className="text-[var(--color-text-primary)] text-sm">{filter.label}</span>
                      {isActive && (
                        <svg className="w-4 h-4 text-[var(--color-primary)]" fill="currentColor" viewBox="0 0 20 20" aria-hidden="true">
                          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                        </svg>
                      )}
                    </button>
                  );
                })}
              </div>
            </div>
          )}
        </div>

        <Button variant="primary" size="md" onClick={() => value.trim() && onSearch?.(value.trim())} disabled={disabled || !value.trim()}>
          Search
        </Button>
      </div>

      {activeFilters.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {activeFilters.map((filterId) => {
            const filter = filters.find((f) => f.id === filterId);
            if (!filter) return null;
            return (
              <span key={filterId} className="inline-flex items-center gap-1 px-2 py-1 bg-[var(--color-primary-container)] text-[var(--color-text-primary)] rounded-full text-xs">
                {filter.icon && <span className="flex-shrink-0">{filter.icon}</span>}
                <span>{filter.label}</span>
                <button
                  type="button"
                  onClick={() => onFilterToggle?.(filterId)}
                  className="p-0.5 hover:bg-[var(--color-surface-tertiary)] rounded-full cursor-pointer"
                  aria-label={`Remove ${filter.label} filter`}
                >
                  <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                    <path d="M6 18L18 6M6 6l12 12" strokeWidth="2" />
                  </svg>
                </button>
              </span>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default SearchBar;
