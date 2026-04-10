"use client";

import { Bell, Zap } from "lucide-react";
import { TopBarMenuItem } from "./top-bar-menu-item";
import { Breadcrumb } from "./breadcrumb";

export type ConnectionStatus = "connected" | "disconnected" | "connecting";

interface TopBarProps {
  currentPath?: string;
  connectionStatus?: ConnectionStatus;
  onOpenPalette?: () => void;
  onNavigate?: (segment: string, index: number) => void;
  notificationCount?: number;
}

const STATUS_COLORS: Record<ConnectionStatus, string> = {
  connected: "var(--status-success)",
  connecting: "var(--status-warning)",
  disconnected: "var(--status-danger)",
};

const STATUS_LABELS: Record<ConnectionStatus, string> = {
  connected: "Connected",
  connecting: "Connecting…",
  disconnected: "Offline",
};

const MENU_ITEMS = ["File", "Edit", "View", "Go", "Terminal", "Help"];

/**
 * Top bar: 36px height.
 * Left: logo + app name + menu items.
 * Center: breadcrumb + Cmd+K trigger.
 * Right: connection dot + notifications.
 */
export function TopBar({
  currentPath = "~/project",
  connectionStatus = "connected",
  onOpenPalette,
  onNavigate,
  notificationCount = 0,
}: TopBarProps) {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        height: "36px",
        padding: "0 0.75rem",
        background: "var(--bg-secondary)",
        borderBottom: "1px solid var(--border-subtle)",
        gap: "0.5rem",
        flexShrink: 0,
        userSelect: "none",
      }}
    >
      {/* Left: Logo + menu items */}
      <div style={{ display: "flex", alignItems: "center", gap: "0.25rem", flexShrink: 0 }}>
        <Zap size={16} style={{ color: "var(--accent-teal-400)" }} />
        <span
          style={{
            fontSize: "0.8rem",
            fontWeight: 700,
            color: "var(--text-primary)",
            marginRight: "0.5rem",
          }}
        >
          Mekong
        </span>
        {MENU_ITEMS.map((item) => (
          <TopBarMenuItem key={item} label={item} />
        ))}
      </div>

      {/* Separator */}
      <div
        style={{
          width: "1px",
          height: "16px",
          background: "var(--border-subtle)",
          flexShrink: 0,
        }}
      />

      {/* Center: breadcrumb + palette trigger */}
      <div
        style={{
          flex: 1,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          gap: "1rem",
          minWidth: 0,
          overflow: "hidden",
        }}
      >
        <Breadcrumb path={currentPath} onNavigate={onNavigate} />

        <button
          onClick={onOpenPalette}
          title="Open command palette (Cmd+K)"
          style={{
            display: "flex",
            alignItems: "center",
            gap: "0.375rem",
            background: "var(--surface-card)",
            border: "1px solid var(--border-subtle)",
            borderRadius: "0.375rem",
            padding: "0.125rem 0.5rem",
            cursor: "pointer",
            color: "var(--text-muted)",
            fontSize: "0.75rem",
            flexShrink: 0,
            transition: "border-color 0.1s",
          }}
        >
          <span style={{ fontSize: "0.7rem" }}>Search commands…</span>
          <kbd
            style={{
              fontSize: "0.65rem",
              background: "var(--bg-tertiary)",
              border: "1px solid var(--border-subtle)",
              borderRadius: "0.2rem",
              padding: "0.05rem 0.3rem",
              fontFamily: "monospace",
              color: "var(--text-muted)",
            }}
          >
            ⌘K
          </kbd>
        </button>
      </div>

      {/* Separator */}
      <div
        style={{
          width: "1px",
          height: "16px",
          background: "var(--border-subtle)",
          flexShrink: 0,
        }}
      />

      {/* Right: connection + notifications */}
      <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", flexShrink: 0 }}>
        {/* Connection status */}
        <div style={{ display: "flex", alignItems: "center", gap: "0.375rem" }}>
          <span
            style={{
              width: "6px",
              height: "6px",
              borderRadius: "50%",
              background: STATUS_COLORS[connectionStatus],
              flexShrink: 0,
            }}
          />
          <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
            {STATUS_LABELS[connectionStatus]}
          </span>
        </div>

        {/* Notifications bell */}
        <button
          title="Notifications"
          style={{
            position: "relative",
            background: "none",
            border: "none",
            cursor: "pointer",
            color: "var(--text-muted)",
            display: "flex",
            alignItems: "center",
            padding: "0.125rem",
            borderRadius: "0.25rem",
          }}
        >
          <Bell size={15} />
          {notificationCount > 0 && (
            <span
              style={{
                position: "absolute",
                top: "-3px",
                right: "-3px",
                background: "var(--status-danger)",
                color: "#fff",
                fontSize: "0.6rem",
                width: "14px",
                height: "14px",
                borderRadius: "50%",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontWeight: 700,
              }}
            >
              {notificationCount > 9 ? "9+" : notificationCount}
            </span>
          )}
        </button>
      </div>
    </div>
  );
}
