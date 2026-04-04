"use client";

import * as React from "react";
import { cn } from "../../lib/utils";

export interface AccessMatrixProps extends React.HTMLAttributes<HTMLDivElement> {
  roles: string[];
  systems: string[];
  permissions: Record<string, Record<string, "allow" | "deny" | "na">>;
}

const cellColor: Record<string, string> = {
  allow: "bg-[var(--perm-allow)]/20 text-[var(--perm-allow)]",
  deny: "bg-[var(--perm-deny)]/20 text-[var(--perm-deny)]",
  na: "bg-[var(--bg-tertiary)] text-[var(--text-muted)]",
};

const cellLabel: Record<string, string> = {
  allow: "\u2713",
  deny: "\u2717",
  na: "\u2014",
};

const AccessMatrix = React.forwardRef<HTMLDivElement, AccessMatrixProps>(
  ({ className, roles, systems, permissions, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        "overflow-x-auto rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--surface-card)]",
        className
      )}
      {...props}
    >
      <table className="w-full border-collapse text-[var(--font-xs)]">
        <thead>
          <tr className="border-b border-[var(--border-default)]">
            <th className="sticky left-0 bg-[var(--surface-card)] px-[var(--spacing-md)] py-[var(--spacing-sm)] text-left font-semibold text-[var(--text-secondary)]">
              Role / System
            </th>
            {systems.map((sys) => (
              <th
                key={sys}
                className="px-[var(--spacing-md)] py-[var(--spacing-sm)] text-center font-semibold text-[var(--text-secondary)]"
              >
                {sys}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {roles.map((role) => (
            <tr
              key={role}
              className="border-b border-[var(--border-default)] last:border-b-0 hover:bg-[var(--surface-hover)]"
            >
              <td className="sticky left-0 bg-[var(--surface-card)] px-[var(--spacing-md)] py-[var(--spacing-sm)] font-medium text-[var(--text-primary)]">
                {role}
              </td>
              {systems.map((sys) => {
                const perm = permissions[role]?.[sys] ?? "na";
                return (
                  <td key={sys} className="px-[var(--spacing-md)] py-[var(--spacing-sm)] text-center">
                    <span
                      className={cn(
                        "inline-flex h-6 w-6 items-center justify-center rounded-[var(--radius-sm)] text-[var(--font-xs)] font-bold",
                        cellColor[perm]
                      )}
                    >
                      {cellLabel[perm]}
                    </span>
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
);
AccessMatrix.displayName = "AccessMatrix";

export { AccessMatrix };
