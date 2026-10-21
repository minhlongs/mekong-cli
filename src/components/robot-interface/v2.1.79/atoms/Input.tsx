/**
 * Input Components - RaaS UX Kit v2.1.79
 * Form input components for robot configuration and system settings
 */
import React, { useState, useRef, useEffect } from 'react';
import { InputProps, TextareaProps } from '../types/robot';

export { Select, Toggle, Slider } from './input-controls';

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
  const hasValue = controlled ? value !== undefined && value !== null && value !== '' : internalValue !== '';

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!controlled) setInternalValue(e.target.value);
    onChange?.(e);
  };

  const handleClear = () => {
    if (!controlled) setInternalValue('');
    onClear?.();
    const input = document.querySelector<HTMLInputElement>(`input[name="${props.name}"]`);
    if (input) input.dispatchEvent(new Event('change', { bubbles: true }));
  };

  const sizeClasses = { sm: 'h-8 text-sm', md: 'h-10 text-base', lg: 'h-12 text-lg' };

  return (
    <div className={`flex flex-col gap-1.5 ${className}`}>
      {label && (
        <label className="text-sm font-medium text-[var(--color-text-secondary)]">
          {label}
          {required && <span className="text-[var(--color-error)] ml-1">*</span>}
        </label>
      )}
      <div
        className={`relative flex items-center border rounded-[var(--radius-input)] transition-all duration-150 ${sizeClasses[size]} ${
          disabled ? 'bg-[var(--color-surface-disabled)] cursor-not-allowed' : 'bg-[var(--color-surface)]'
        } ${readOnly ? 'bg-transparent' : ''} ${
          error
            ? 'border-[var(--color-error)] focus-within:border-[var(--color-error)] focus-within:ring-2 focus-within:ring-[var(--color-error)]'
            : isFocused
            ? 'border-[var(--color-primary)] ring-2 ring-[var(--color-focus-ring)]'
            : 'border-[var(--color-border)]'
        }`}
      >
        {prefix && <span className="pl-3 pr-2 text-[var(--color-text-tertiary)]">{prefix}</span>}
        <input
          type={type}
          className={`flex-1 bg-transparent outline-none text-[var(--color-text-primary)] placeholder-[var(--color-text-disabled)] disabled:cursor-not-allowed ${
            prefix ? 'pl-0' : 'pl-3'
          } ${suffix || clearable ? 'pr-0' : 'pr-3'}`}
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
        {clearable && hasValue && !disabled && !readOnly && (
          <button
            type="button"
            onClick={handleClear}
            className="p-2 text-[var(--color-text-tertiary)] hover:text-[var(--color-text-secondary)] cursor-pointer"
            aria-label="Clear input"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        )}
        {suffix && !clearable && <span className="pr-3 pl-2 text-[var(--color-text-tertiary)]">{suffix}</span>}
      </div>
      {(helperText || error) && (
        <span className={`text-xs ${error ? 'text-[var(--color-error)]' : 'text-[var(--color-text-tertiary)]'}`}>
          {error || helperText}
        </span>
      )}
    </div>
  );
};

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

  useEffect(() => {
    if (autoResize && textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, maxRows * 24)}px`;
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
        className={`w-full px-3 py-2 bg-[var(--color-surface)] border rounded-[var(--radius-input)] transition-all duration-150 text-[var(--color-text-primary)] placeholder-[var(--color-text-disabled)] outline-none resize-none disabled:bg-[var(--color-surface-disabled)] disabled:cursor-not-allowed ${
          error
            ? 'border-[var(--color-error)] focus:border-[var(--color-error)] focus:ring-2 focus:ring-[var(--color-error)]'
            : isFocused
            ? 'border-[var(--color-primary)] ring-2 ring-[var(--color-focus-ring)]'
            : 'border-[var(--color-border)]'
        }`}
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

export default Input;
