"use client";

import { useState } from "react";

interface TopBarMenuItemProps {
  label: string;
  onClick?: () => void;
}

/**
 * Single menu item in the top bar (File, Edit, View, etc.).
 * Hover shows subtle highlight. Dropdown is placeholder for future phases.
 */
export function TopBarMenuItem({ label, onClick }: TopBarMenuItemProps) {
  const [hovered, setHovered] = useState(false);

  return (
    <button
      onClick={onClick}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        background: hovered ? "var(--surface-hover)" : "transparent",
        border: "none",
        cursor: "pointer",
        color: hovered ? "var(--text-primary)" : "var(--text-secondary)",
        fontSize: "0.8rem",
        padding: "0.25rem 0.5rem",
        borderRadius: "0.25rem",
        transition: "background 0.1s, color 0.1s",
        whiteSpace: "nowrap",
        fontFamily: "inherit",
      }}
    >
      {label}
    </button>
  );
}
