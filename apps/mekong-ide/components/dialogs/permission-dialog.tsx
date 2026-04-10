"use client";

import { useState } from "react";
import { AlertTriangle, X } from "lucide-react";
import { Button } from "@/components/ds";
import { PermissionDetailRow } from "./permission-detail-row";

export type RiskLevel = "low" | "medium" | "high" | "critical";

export interface PermissionRequest {
  command: string;
  tool: string;
  workingDir?: string;
  riskLevel: RiskLevel;
  description?: string;
  agentName?: string;
}

interface PermissionDialogProps {
  request: PermissionRequest;
  onApprove: (alwaysAllow: boolean) => void;
  onDeny: () => void;
  onClose?: () => void;
}

const RISK_LABELS: Record<RiskLevel, string> = {
  low: "Low",
  medium: "Medium",
  high: "High",
  critical: "Critical",
};

/**
 * Permission dialog (520x400 card).
 * Shows command, detail rows, and approve/deny controls.
 * "Always allow" checkbox grants permanent permission for this tool.
 */
export function PermissionDialog({
  request,
  onApprove,
  onDeny,
  onClose,
}: PermissionDialogProps) {
  const [alwaysAllow, setAlwaysAllow] = useState(false);

  return (
    /* Backdrop */
    <div
      onClick={onClose ?? onDeny}
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 10000,
        background: "rgba(0,0,0,0.65)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      {/* Card */}
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="perm-dialog-title"
        onClick={(e) => e.stopPropagation()}
        style={{
          width: "min(520px, calc(100vw - 2rem))",
          background: "var(--surface-card)",
          border: "1px solid var(--border-strong)",
          borderRadius: "0.75rem",
          overflow: "hidden",
          boxShadow: "0 24px 64px rgba(0,0,0,0.7)",
        }}
      >
        {/* Header */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            padding: "1rem 1.25rem",
            borderBottom: "1px solid var(--border-subtle)",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "0.625rem" }}>
            <AlertTriangle
              size={18}
              style={{ color: "var(--status-warning)", flexShrink: 0 }}
            />
            <span
              id="perm-dialog-title"
              style={{ fontSize: "0.95rem", fontWeight: 600, color: "var(--text-primary)" }}
            >
              Permission Required
            </span>
          </div>
          {onClose && (
            <button
              onClick={onClose}
              aria-label="Close dialog"
              style={{
                background: "none",
                border: "none",
                cursor: "pointer",
                color: "var(--text-muted)",
                display: "flex",
                padding: "0.25rem",
                borderRadius: "0.25rem",
              }}
            >
              <X size={16} />
            </button>
          )}
        </div>

        {/* Body */}
        <div style={{ padding: "1.25rem" }}>
          {/* Command block */}
          <div
            style={{
              background: "var(--bg-tertiary)",
              border: "1px solid var(--border-subtle)",
              borderRadius: "0.5rem",
              padding: "0.75rem 1rem",
              marginBottom: "1.25rem",
              overflowX: "auto",
            }}
          >
            <code
              style={{
                fontFamily: "monospace",
                fontSize: "0.85rem",
                color: "var(--text-primary)",
                whiteSpace: "pre",
              }}
            >
              {`$ ${request.command}`}
            </code>
          </div>

          {/* Detail rows */}
          <div
            style={{
              borderTop: "1px solid var(--border-subtle)",
              borderBottom: "1px solid var(--border-subtle)",
              marginBottom: "1.25rem",
            }}
          >
            <PermissionDetailRow label="Tool" value={request.tool} />
            <PermissionDetailRow
              label="Risk"
              value={RISK_LABELS[request.riskLevel]}
              riskLevel={request.riskLevel}
            />
            {request.workingDir && (
              <PermissionDetailRow label="Scope" value={request.workingDir} />
            )}
            {request.agentName && (
              <PermissionDetailRow label="Agent" value={request.agentName} />
            )}
            {request.description && (
              <PermissionDetailRow label="Details" value={request.description} />
            )}
          </div>

          {/* Always allow checkbox */}
          <label
            style={{
              display: "flex",
              alignItems: "center",
              gap: "0.5rem",
              cursor: "pointer",
              marginBottom: "1.25rem",
            }}
          >
            <input
              type="checkbox"
              checked={alwaysAllow}
              onChange={(e) => setAlwaysAllow(e.target.checked)}
              style={{ accentColor: "var(--accent-teal-500)", width: "14px", height: "14px" }}
            />
            <span style={{ fontSize: "0.85rem", color: "var(--text-secondary)" }}>
              Always allow this tool
            </span>
          </label>

          {/* Footer buttons */}
          <div style={{ display: "flex", justifyContent: "flex-end", gap: "0.75rem" }}>
            <Button variant="ghost" size="md" onClick={onDeny}>
              Deny
            </Button>
            <Button variant="primary" size="md" onClick={() => onApprove(alwaysAllow)}>
              Approve
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
