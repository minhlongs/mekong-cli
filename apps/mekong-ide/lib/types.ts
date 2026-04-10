// Shared TypeScript types for Mekong IDE design system

export type Size = "sm" | "md" | "lg";
export type StatusVariant = "success" | "warning" | "danger" | "info";
export type ModelVariant = "architect" | "reasoning" | "audit" | "trading";
export type ButtonVariant = "primary" | "secondary" | "danger" | "ghost";
export type BadgeVariant = StatusVariant | ModelVariant;

export interface TableColumn {
  key: string;
  label: string;
  width?: string;
}

export interface TableRow {
  [key: string]: React.ReactNode;
}

export interface ToastItem {
  id: string;
  message: string;
  variant: StatusVariant;
  duration?: number;
}
