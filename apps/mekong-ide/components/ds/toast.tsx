"use client";
import { useEffect } from "react";
import { CheckCircle, XCircle, AlertCircle, Info, X } from "lucide-react";
import type { StatusVariant } from "@/lib/types";

interface ToastProps {
  id: string;
  message: string;
  variant: StatusVariant;
  duration?: number;
  onDismiss: (id: string) => void;
}

const iconMap: Record<StatusVariant, React.ReactNode> = {
  success: <CheckCircle size={16} />,
  danger:  <XCircle size={16} />,
  warning: <AlertCircle size={16} />,
  info:    <Info size={16} />,
};

const colorVarMap: Record<StatusVariant, string> = {
  success: "var(--status-success)",
  danger:  "var(--status-danger)",
  warning: "var(--status-warning)",
  info:    "var(--status-info)",
};

export function Toast({ id, message, variant, duration = 3000, onDismiss }: ToastProps) {
  useEffect(() => {
    if (duration <= 0) return;
    const t = setTimeout(() => onDismiss(id), duration);
    return () => clearTimeout(t);
  }, [id, duration, onDismiss]);

  const color = colorVarMap[variant];

  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: "0.625rem",
        padding: "0.75rem 1rem",
        background: "var(--surface-card)",
        border: `1px solid ${color}`,
        borderRadius: "0.5rem",
        minWidth: "18rem",
        maxWidth: "24rem",
        boxShadow: "0 4px 12px rgba(0,0,0,0.4)",
        color,
      }}
    >
      {iconMap[variant]}
      <span style={{ flex: 1, fontSize: "0.875rem", color: "var(--text-primary)" }}>{message}</span>
      <button
        onClick={() => onDismiss(id)}
        style={{ background: "none", border: "none", cursor: "pointer", color: "var(--text-muted)", display: "flex" }}
      >
        <X size={14} />
      </button>
    </div>
  );
}

interface ToastContainerProps {
  toasts: Array<{ id: string; message: string; variant: StatusVariant; duration?: number }>;
  onDismiss: (id: string) => void;
}

export function ToastContainer({ toasts, onDismiss }: ToastContainerProps) {
  return (
    <div
      style={{
        position: "fixed",
        bottom: "1.5rem",
        right: "1.5rem",
        display: "flex",
        flexDirection: "column",
        gap: "0.5rem",
        zIndex: 9999,
      }}
    >
      {toasts.map((t) => (
        <Toast key={t.id} {...t} onDismiss={onDismiss} />
      ))}
    </div>
  );
}
