"use client";
import { useState } from "react";

interface ToggleProps {
  defaultChecked?: boolean;
  checked?: boolean;
  onChange?: (value: boolean) => void;
  label?: string;
  disabled?: boolean;
}

export function Toggle({ defaultChecked = false, checked, onChange, label, disabled = false }: ToggleProps) {
  const [internal, setInternal] = useState(defaultChecked);
  const isOn = checked !== undefined ? checked : internal;

  const handleClick = () => {
    if (disabled) return;
    const next = !isOn;
    if (checked === undefined) setInternal(next);
    onChange?.(next);
  };

  return (
    <label
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: "0.5rem",
        cursor: disabled ? "not-allowed" : "pointer",
        opacity: disabled ? 0.5 : 1,
      }}
    >
      <button
        role="switch"
        aria-checked={isOn}
        aria-label={label}
        onClick={handleClick}
        disabled={disabled}
        style={{
          width: "2.5rem",
          height: "1.375rem",
          borderRadius: "9999px",
          background: isOn ? "var(--accent-teal-500)" : "var(--border-strong)",
          border: "none",
          cursor: disabled ? "not-allowed" : "pointer",
          position: "relative",
          transition: "background 0.2s",
          padding: 0,
          flexShrink: 0,
        }}
      >
        <span
          style={{
            position: "absolute",
            top: "0.1875rem",
            left: isOn ? "1.1875rem" : "0.1875rem",
            width: "1rem",
            height: "1rem",
            borderRadius: "50%",
            background: "#fff",
            transition: "left 0.2s",
            boxShadow: "0 1px 3px rgba(0,0,0,0.3)",
          }}
        />
      </button>
      {label && (
        <span style={{ fontSize: "0.875rem", color: "var(--text-secondary)" }}>{label}</span>
      )}
    </label>
  );
}
