/**
 * Input Components - RaaS UX Kit v2.1.79
 * Form input components for robot configuration and system settings
 */

import React, { useState, useCallback, useRef, useEffect } from 'react';
import {
  InputProps,
  TextareaProps,
  SelectProps,
  SelectOption,
  ToggleProps,
  SliderProps,
} from '../types/robot';

// ============================================
// Text Input
// ============================================

export const Input: React.FC<InputProps> = ({
  type = 'text',
  size = 'md',
  label,
  error,
  helperText,
  prefix,
  suffix,
  clearable = false,
  onClear,
  className = '',
  value,
  onChange,
  disabled,
  readOnly,
  required,
  placeholder,
  ...props
}) => {
  const [isFocused, setIsFocused] = useState(false);
  const [internalValue, setInternalValue] = useState(value?.toString() || '');

  const controlled = value !== undefined;
  const currentValue = controlled ? value : internalValue;
  const hasValue = controlled
    ? value !== undefined && value !== null && value !== ''
    : internalValue !== '';

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!controlled) {
      setInternalValue(e.target.value);
    }
    onChange?.(e);
  };

  const handleClear = () => {
    if (!controlled) {
      setInternalValue('');
    }
    onClear?.();
    // Dispatch change event with empty value
    const input = document.querySelector<HTMLInputElement>(
      `input[name="${props.name}"]`
    );
    if (input) {
      input.dispatchEvent(new Event('change', { bubbles: true }));
    }
  };

  // Size mappings
  const sizeClasses = {
    sm: 'h-8 text-sm',
    md: 'h-10 text-base',
    lg: 'h-12 text-lg',
  };

  return (
    <div className={`flex flex-col gap-1.5 ${className}`}>
      {/* Label */}
      {label && (
        <label className="text-sm font-medium text-[var(--color-text-secondary)]">
          {label}
          {required && <span className="text-[var(--color-error)] ml-1">*</span>}
        </label>
      )}

      {/* Input Container */}
      <div
        className={`
          relative flex items-center
          border rounded-[var(--radius-input)]
          transition-all duration-150
          ${sizeClasses[size]}
          ${disabled ? 'bg-[var(--color-surface-disabled)] cursor-not-allowed' : 'bg-[var(--color-surface)]'}
          ${readOnly ? 'bg-transparent' : ''}
          ${
            error
              ? 'border-[var(--color-error)] focus-within:border-[var(--color-error)] focus-within:ring-2 focus-within:ring-[var(--color-error)]'
              : isFocused
              ? 'border-[var(--color-primary)] ring-2 ring-[var(--color-focus-ring)]'
              : 'border-[var(--color-border)]'
          }
        `}
      >
        {/* Prefix */}
        {prefix && (
          <span className="pl-3 pr-2 text-[var(--color-text-tertiary)]">
            {prefix}
          </span>
        )}

        {/* Input Field */}
        <input
          type={type}
          className={`
            flex-1 bg-transparent outline-none
            text-[var(--color-text-primary)]
            placeholder-[var(--color-text-disabled)]
            disabled:cursor-not-allowed
            ${prefix ? 'pl-0' : 'pl-3'}
            ${suffix || clearable ? 'pr-0' : 'pr-3'}
          `}
          value={currentValue}
          onChange={handleChange}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          disabled={disabled}
          readOnly={readOnly}
          required={required}
          placeholder={placeholder}
          {...props}
        />

        {/* Clear Button */}
        {clearable && hasValue && !disabled && !readOnly && (
          <button
            type="button"
            onClick={handleClear}
            className="p-2 text-[var(--color-text-tertiary)] hover:text-[var(--color-text-secondary)]"
            aria-label="Clear input"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        )}

        {/* Suffix */}
        {suffix && !clearable && (
          <span className="pr-3 pl-2 text-[var(--color-text-tertiary)]">
            {suffix}
          </span>
        )}
      </div>

      {/* Helper Text / Error */}
      {(helperText || error) && (
        <span className={`text-xs ${error ? 'text-[var(--color-error)]' : 'text-[var(--color-text-tertiary)]'}`}>
          {error || helperText}
        </span>
      )}
    </div>
  );
};

// ============================================
// Textarea
// ============================================

export const Textarea: React.FC<TextareaProps> = ({
  label,
  error,
  helperText,
  rows = 3,
  maxRows = 10,
  autoResize = false,
  className = '',
  value,
  onChange,
  disabled,
  readOnly,
  required,
  placeholder,
  ...props
}) => {
  const [isFocused, setIsFocused] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize logic
  useEffect(() => {
    if (autoResize && textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      const scrollHeight = textareaRef.current.scrollHeight;
      const maxHeight = maxRows * 24; // Approximate line height
      textareaRef.current.style.height = `${Math.min(scrollHeight, maxHeight)}px`;
    }
  }, [value, autoResize, maxRows]);

  return (
    <div className={`flex flex-col gap-1.5 ${className}`}>
      {label && (
        <label className="text-sm font-medium text-[var(--color-text-secondary)]">
          {label}
          {required && <span className="text-[var(--color-error)] ml-1">*</span>}
        </label>
      )}

      <textarea
        ref={textareaRef}
        rows={rows}
        className={`
          w-full px-3 py-2
          bg-[var(--color-surface)]
          border rounded-[var(--radius-input)]
          transition-all duration-150
          text-[var(--color-text-primary)]
          placeholder-[var(--color-text-disabled)]
          outline-none resize-none
          disabled:bg-[var(--color-surface-disabled)] disabled:cursor-not-allowed
          ${
            error
              ? 'border-[var(--color-error)] focus:border-[var(--color-error)] focus:ring-2 focus:ring-[var(--color-error)]'
              : isFocused
              ? 'border-[var(--color-primary)] ring-2 ring-[var(--color-focus-ring)]'
              : 'border-[var(--color-border)]'
          }
        `}
        value={value}
        onChange={onChange}
        onFocus={() => setIsFocused(true)}
        onBlur={() => setIsFocused(false)}
        disabled={disabled}
        readOnly={readOnly}
        required={required}
        placeholder={placeholder}
        {...props}
      />

      {(helperText || error) && (
        <span className={`text-xs ${error ? 'text-[var(--color-error)]' : 'text-[var(--color-text-tertiary)]'}`}>
          {error || helperText}
        </span>
      )}
    </div>
  );
};

// ============================================
// Select
// ============================================

export const Select: React.FC<SelectProps> = ({
  label,
  error,
  helperText,
  options = [],
  value,
  onChange,
  placeholder,
  searchable = false,
  multi = false,
  className = '',
  disabled,
  required,
  ...props
}) => {
  const [isFocused, setIsFocused] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  const selectRef = useRef<HTMLDivElement>(null);

  // Filter options when searchable
  const filteredOptions = searchable
    ? options.filter((opt) =>
        opt.label.toLowerCase().includes(searchTerm.toLowerCase())
      )
    : options;

  // Close dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (selectRef.current && !selectRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSelect = (selectedValue: string) => {
    if (multi) {
      // Multi-select logic would go here
      const event = { target: { value: selectedValue } } as React.ChangeEvent<HTMLSelectElement>;
      onChange?.(event);
    } else {
      const event = { target: { value: selectedValue } } as React.ChangeEvent<HTMLSelectElement>;
      onChange?.(event);
      setIsOpen(false);
    }
  };

  const selectedOption = options.find((opt) => opt.value === value);

  return (
    <div className={`relative flex flex-col gap-1.5 ${className}`} ref={selectRef}>
      {label && (
        <label className="text-sm font-medium text-[var(--color-text-secondary)]">
          {label}
          {required && <span className="text-[var(--color-error)] ml-1">*</span>}
        </label>
      )}

      {/* Select Trigger */}
      <div
        className={`
          relative flex items-center justify-between
          h-10 px-3
          border rounded-[var(--radius-input)]
          cursor-pointer
          transition-all duration-150
          ${disabled ? 'bg-[var(--color-surface-disabled)] cursor-not-allowed' : 'bg-[var(--color-surface)]'}
          ${
            error
              ? 'border-[var(--color-error)]'
              : isFocused
              ? 'border-[var(--color-primary)] ring-2 ring-[var(--color-focus-ring)]'
              : 'border-[var(--color-border)]'
          }
        `}
        onClick={() => !disabled && setIsOpen(!isOpen)}
      >
        <span className={selectedOption ? 'text-[var(--color-text-primary)]' : 'text-[var(--color-text-disabled)]'}>
          {selectedOption?.label || placeholder || 'Select...'}
        </span>
        <svg
          className={`w-4 h-4 text-[var(--color-text-tertiary)] transition-transform ${isOpen ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </div>

      {/* Dropdown */}
      {isOpen && (
        <div
          className="absolute top-full left-0 right-auto mt-1 max-h-60 overflow-auto bg-[var(--color-surface)] border border-[var(--color-border)] rounded-[var(--radius-md)] shadow-lg z-50"
          style={{ minWidth: '200px' }}
        >
          {searchable && (
            <div className="p-2 border-b border-[var(--color-border)]">
              <input
                type="text"
                className="w-full px-2 py-1 text-sm bg-transparent outline-none"
                placeholder="Search..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                onClick={(e) => e.stopPropagation()}
              />
            </div>
          )}

          <div className="py-1">
            {filteredOptions.map((option) => (
              <button
                key={option.value}
                className={`
                  w-full px-3 py-2 text-left flex items-center gap-2
                  hover:bg-[var(--color-surface-tertiary)]
                  ${option.disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
                  ${option.value === value ? 'bg-[var(--color-primary-container)]' : ''}
                `}
                onClick={() => !option.disabled && handleSelect(option.value)}
                disabled={option.disabled}
              >
                {option.icon && <span className="flex-shrink-0">{option.icon}</span>}
                <span className="flex-1 text-[var(--color-text-primary)]">{option.label}</span>
              </button>
            ))}
          </div>
        </div>
      )}

      {(helperText || error) && (
        <span className={`text-xs ${error ? 'text-[var(--color-error)]' : 'text-[var(--color-text-tertiary)]'}`}>
          {error || helperText}
        </span>
      )}
    </div>
  );
};

// ============================================
// Toggle (Switch)
// ============================================

export const Toggle: React.FC<ToggleProps> = ({
  checked,
  onChange,
  label,
  size = 'md',
  disabled = false,
  labels,
  variant = 'default',
  confirmRequired = false,
  confirmMessage,
  className = '',
}) => {
  const [pendingState, setPendingState] = useState<boolean | null>(null);

  const sizeClasses = {
    sm: 'w-8 h-4',
    md: 'w-11 h-6',
    lg: 'w-14 h-8',
  };

  const thumbSizes = {
    sm: 'w-3 h-3',
    md: 'w-5 h-5',
    lg: 'w-6 h-6',
  };

  const translateClasses = {
    sm: checked ? 'translate-x-4' : 'translate-x-0',
    md: checked ? 'translate-x-5' : 'translate-x-0',
    lg: checked ? 'translate-x-7' : 'translate-x-0',
  };

  const variantColors = {
    default: {
      on: 'bg-[var(--color-primary)]',
      off: 'bg-[var(--color-surface-tertiary)]',
    },
    success: {
      on: 'bg-[var(--color-success)]',
      off: 'bg-[var(--color-surface-tertiary)]',
    },
    danger: {
      on: 'bg-[var(--color-error)]',
      off: 'bg-[var(--color-surface-tertiary)]',
    },
  };

  const handleChange = () => {
    if (disabled) return;

    if (confirmRequired && !checked) {
      const confirmed = window.confirm(confirmMessage || 'Are you sure?');
      if (!confirmed) return;
    }

    onChange(!checked);
  };

  return (
    <div className={`flex items-center gap-3 ${className}`}>
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        disabled={disabled}
        onClick={handleChange}
        className={`
          relative inline-flex items-center
          rounded-full transition-colors duration-200
          focus:outline-none focus:ring-2 focus:ring-[var(--color-focus-ring)] focus:ring-offset-2
          ${sizeClasses[size]}
          ${checked ? variantColors[variant].on : variantColors[variant].off}
          ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
        `}
      >
        <span
          className={`
            inline-block bg-[var(--color-surface)]
            rounded-full transition-transform duration-200
            ${thumbSizes[size]}
            ${translateClasses[size]}
          `}
        />
      </button>

      {(label || labels) && (
        <span className="text-sm text-[var(--color-text-primary)]">
          {label || (checked ? labels?.on : labels?.off)}
        </span>
      )}
    </div>
  );
};

// ============================================
// Slider
// ============================================

export const Slider: React.FC<SliderProps> = ({
  value,
  onChange,
  min = 0,
  max = 100,
  step = 1,
  label,
  unit,
  marks,
  renderMark,
  warningThreshold,
  range = false,
  disabled = false,
  className = '',
}) => {
  const percentage = ((value - min) / (max - min)) * 100;

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!disabled) {
      onChange(Number(e.target.value));
    }
  };

  return (
    <div className={`flex flex-col gap-2 ${className}`}>
      {/* Label with Value */}
      {label && (
        <div className="flex justify-between items-center">
          <label className="text-sm font-medium text-[var(--color-text-secondary)]">
            {label}
          </label>
          <span className="text-sm font-mono text-[var(--color-text-primary)]">
            {value}
            {unit && <span className="ml-1 text-[var(--color-text-tertiary)]">{unit}</span>}
          </span>
        </div>
      )}

      {/* Slider Container */}
      <div className="relative h-6 flex items-center">
        {/* Track */}
        <div className="absolute w-full h-1.5 bg-[var(--color-surface-tertiary)] rounded-full" />

        {/* Fill */}
        <div
          className={`absolute h-1.5 rounded-full transition-all ${
            warningThreshold && percentage >= warningThreshold
              ? 'bg-[var(--color-caution)]'
              : 'bg-[var(--color-primary)]'
          }`}
          style={{ width: `${percentage}%` }}
        />

        {/* Input */}
        <input
          type="range"
          min={min}
          max={max}
          step={step}
          value={value}
          onChange={handleChange}
          disabled={disabled}
          className="absolute w-full h-full opacity-0 cursor-pointer disabled:cursor-not-allowed"
          style={{ zIndex: 10 }}
        />

        {/* Thumb */}
        <div
          className={`
            absolute w-5 h-5 bg-[var(--color-surface)]
            border-2 border-[var(--color-primary)]
            rounded-full shadow-md
            pointer-events-none
            transition-all
            ${disabled ? 'opacity-50' : ''}
          `}
          style={{
            left: `calc(${percentage}% - 10px)`,
            zIndex: 5,
          }}
        />
      </div>

      {/* Marks */}
      {marks && marks.length > 0 && (
        <div className="relative h-4 flex justify-between">
          {marks.map((mark, index) => {
            const markPercentage = ((mark - min) / (max - min)) * 100;
            return (
              <div
                key={index}
                className="absolute flex flex-col items-center gap-1"
                style={{ left: `${markPercentage}%`, transform: 'translateX(-50%)' }}
              >
                <div className="w-0.5 h-2 bg-[var(--color-border)]" />
                {renderMark && (
                  <span className="text-xs text-[var(--color-text-tertiary)]">
                    {renderMark(mark)}
                  </span>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default Input;
