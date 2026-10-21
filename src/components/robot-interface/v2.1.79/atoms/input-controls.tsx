/**
 * Input Control Subcomponents (Select, Toggle, Slider) - RaaS UX Kit v2.1.79
 */
import React, { useState, useRef, useEffect } from 'react';
import { SelectProps, ToggleProps, SliderProps } from '../types/robot';

export const Select: React.FC<SelectProps> = ({
  label, error, helperText, options = [], value, onChange, placeholder, searchable = false, className = '', disabled, required,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  const selectRef = useRef<HTMLDivElement>(null);

  const filteredOptions = searchable ? options.filter((opt) => opt.label.toLowerCase().includes(searchTerm.toLowerCase())) : options;

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (selectRef.current && !selectRef.current.contains(e.target as Node)) setIsOpen(false);
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSelect = (selectedValue: string) => {
    onChange?.({ target: { value: selectedValue } } as React.ChangeEvent<HTMLSelectElement>);
    setIsOpen(false);
  };

  const selectedOption = options.find((opt) => opt.value === value);

  return (
    <div className={`relative flex flex-col gap-1.5 ${className}`} ref={selectRef}>
      {label && (
        <label className="text-sm font-medium text-[var(--color-text-secondary)]">
          {label}{required && <span className="text-[var(--color-error)] ml-1">*</span>}
        </label>
      )}
      <div
        className={`relative flex items-center justify-between h-10 px-3 border rounded-[var(--radius-input)] transition-all duration-150 ${
          disabled ? 'bg-[var(--color-surface-disabled)] cursor-not-allowed' : 'bg-[var(--color-surface)] cursor-pointer'
        } ${error ? 'border-[var(--color-error)]' : 'border-[var(--color-border)]'}`}
        onClick={() => !disabled && setIsOpen(!isOpen)}
      >
        <span className={selectedOption ? 'text-[var(--color-text-primary)]' : 'text-[var(--color-text-disabled)]'}>
          {selectedOption?.label || placeholder || 'Select...'}
        </span>
        <svg className={`w-4 h-4 text-[var(--color-text-tertiary)] transition-transform ${isOpen ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </div>
      {isOpen && (
        <div className="absolute top-full left-0 right-auto mt-1 max-h-60 overflow-auto bg-[var(--color-surface)] border border-[var(--color-border)] rounded-[var(--radius-md)] shadow-lg z-50 min-w-[200px]">
          {searchable && (
            <div className="p-2 border-b border-[var(--color-border)]">
              <input
                type="text" className="w-full px-2 py-1 text-sm bg-transparent outline-none" placeholder="Search..."
                value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} onClick={(e) => e.stopPropagation()}
              />
            </div>
          )}
          <div className="py-1">
            {filteredOptions.map((option) => (
              <button
                key={option.value} type="button" disabled={option.disabled}
                className={`w-full px-3 py-2 text-left flex items-center gap-2 hover:bg-[var(--color-surface-tertiary)] ${
                  option.disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'
                } ${option.value === value ? 'bg-[var(--color-primary-container)]' : ''}`}
                onClick={() => !option.disabled && handleSelect(option.value)}
              >
                {option.icon && <span className="flex-shrink-0">{option.icon}</span>}
                <span className="flex-1 text-[var(--color-text-primary)]">{option.label}</span>
              </button>
            ))}
          </div>
        </div>
      )}
      {(helperText || error) && <span className={`text-xs ${error ? 'text-[var(--color-error)]' : 'text-[var(--color-text-tertiary)]'}`}>{error || helperText}</span>}
    </div>
  );
};

export const Toggle: React.FC<ToggleProps> = ({
  checked, onChange, label, size = 'md', disabled = false, labels, variant = 'default', confirmRequired = false, confirmMessage, className = '',
}) => {
  const sizeClasses = { sm: 'w-8 h-4', md: 'w-11 h-6', lg: 'w-14 h-8' };
  const thumbSizes = { sm: 'w-3 h-3', md: 'w-5 h-5', lg: 'w-6 h-6' };
  const translateClasses = { sm: checked ? 'translate-x-4' : 'translate-x-0', md: checked ? 'translate-x-5' : 'translate-x-0', lg: checked ? 'translate-x-7' : 'translate-x-0' };
  const variantColors = {
    default: { on: 'bg-[var(--color-primary)]', off: 'bg-[var(--color-surface-tertiary)]' },
    success: { on: 'bg-[var(--color-success)]', off: 'bg-[var(--color-surface-tertiary)]' },
    danger: { on: 'bg-[var(--color-error)]', off: 'bg-[var(--color-surface-tertiary)]' },
  };
  return (
    <div className={`flex items-center gap-3 ${className}`}>
      <button
        type="button" role="switch" aria-checked={checked} disabled={disabled}
        onClick={() => {
          if (disabled || (confirmRequired && !checked && !window.confirm(confirmMessage || 'Are you sure?'))) return;
          onChange(!checked);
        }}
        className={`relative inline-flex items-center rounded-full transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-[var(--color-focus-ring)] focus:ring-offset-2 ${
          sizeClasses[size]
        } ${checked ? variantColors[variant].on : variantColors[variant].off} ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
      >
        <span className={`inline-block bg-[var(--color-surface)] rounded-full transition-transform duration-200 ${thumbSizes[size]} ${translateClasses[size]}`} />
      </button>
      {(label || labels) && <span className="text-sm text-[var(--color-text-primary)]">{label || (checked ? labels?.on : labels?.off)}</span>}
    </div>
  );
};

export const Slider: React.FC<SliderProps> = ({
  value, onChange, min = 0, max = 100, step = 1, label, unit, marks, renderMark, warningThreshold, disabled = false, className = '',
}) => {
  const percentage = ((value - min) / (max - min)) * 100;
  return (
    <div className={`flex flex-col gap-2 ${className}`}>
      {label && (
        <div className="flex justify-between items-center">
          <label className="text-sm font-medium text-[var(--color-text-secondary)]">{label}</label>
          <span className="text-sm font-mono tabular-nums text-[var(--color-text-primary)]">{value}{unit && <span className="ml-1 text-[var(--color-text-tertiary)]">{unit}</span>}</span>
        </div>
      )}
      <div className="relative h-6 flex items-center">
        <div className="absolute w-full h-1.5 bg-[var(--color-surface-tertiary)] rounded-full" />
        <div className={`absolute h-1.5 rounded-full transition-all ${warningThreshold && percentage >= warningThreshold ? 'bg-[var(--color-caution)]' : 'bg-[var(--color-primary)]'}`} style={{ width: `${percentage}%` }} />
        <input type="range" min={min} max={max} step={step} value={value} disabled={disabled} onChange={(e) => !disabled && onChange(Number(e.target.value))} className="absolute w-full h-full opacity-0 cursor-pointer disabled:cursor-not-allowed z-10" />
        <div className={`absolute w-5 h-5 bg-[var(--color-surface)] border-2 border-[var(--color-primary)] rounded-full shadow-md pointer-events-none transition-all z-[5] ${disabled ? 'opacity-50' : ''}`} style={{ left: `calc(${percentage}% - 10px)` }} />
      </div>
      {marks && marks.length > 0 && (
        <div className="relative h-4 flex justify-between">
          {marks.map((mark, index) => (
            <div key={index} className="absolute flex flex-col items-center gap-1" style={{ left: `${((mark - min) / (max - min)) * 100}%`, transform: 'translateX(-50%)' }}>
              <div className="w-0.5 h-2 bg-[var(--color-border)]" />
              {renderMark && <span className="text-xs text-[var(--color-text-tertiary)]">{renderMark(mark)}</span>}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
