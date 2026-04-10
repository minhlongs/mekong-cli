"use client";

import {
  Folder,
  Search,
  Bot,
  Cpu,
  ListTodo,
  TrendingUp,
  Settings,
  User,
} from "lucide-react";
import { LeftSidebarNavItem } from "./left-sidebar-nav-item";

interface LeftSidebarProps {
  /** Currently active nav section */
  activeSection?: string;
  onSectionChange?: (section: string) => void;
}

const TOP_NAV_ITEMS = [
  { id: "explorer", icon: Folder, label: "Explorer" },
  { id: "search", icon: Search, label: "Search" },
  { id: "agent", icon: Bot, label: "Agent" },
  { id: "engine", icon: Cpu, label: "Engine Farm" },
  { id: "tasks", icon: ListTodo, label: "Tasks" },
  { id: "trading", icon: TrendingUp, label: "CashClaw" },
] as const;

/**
 * 48px vertical icon navigation rail.
 * Logo at top, main nav icons, settings + user avatar at bottom.
 */
export function LeftSidebar({
  activeSection = "explorer",
  onSectionChange,
}: LeftSidebarProps) {
  return (
    <aside
      className="w-12 flex flex-col h-full shrink-0"
      style={{
        backgroundColor: "var(--bg-secondary)",
        borderRight: "1px solid var(--border-subtle)",
      }}
    >
      {/* Logo */}
      <div className="w-12 h-12 flex items-center justify-center shrink-0">
        <div
          className="w-7 h-7 rounded flex items-center justify-center text-xs font-bold"
          style={{
            backgroundColor: "var(--accent-teal-500)",
            color: "var(--bg-primary)",
          }}
        >
          M
        </div>
      </div>

      {/* Top nav items */}
      <nav className="flex flex-col flex-1 pt-2">
        {TOP_NAV_ITEMS.map(({ id, icon, label }) => (
          <LeftSidebarNavItem
            key={id}
            icon={icon}
            label={label}
            active={activeSection === id}
            onClick={() => onSectionChange?.(id)}
          />
        ))}
      </nav>

      {/* Bottom: Settings + User */}
      <div className="flex flex-col pb-2">
        <LeftSidebarNavItem icon={Settings} label="Settings" />
        <LeftSidebarNavItem icon={User} label="Profile" />
      </div>
    </aside>
  );
}
