"use client";

import * as React from "react";
import { cn } from "../../lib/utils";

export interface AccessMatrixProps extends React.HTMLAttributes<HTMLDivElement> {
  roles: string[];
  systems: string[];
  permissions: Record<string, Record<string, "allow" | "deny" | "na">>;
}

const cellColor: Record<string, string> = {
  allow: "bg-[var(-PermAllow)]/20 text-[var(-PermAllow)]",
  deny: "bg-[var(-PermDeny)]/20 text-[var(-PermDeny)]",
  na: "bg-[var(-BgTertiary)] text-[var(-TextMuted)]",
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
        "overflowXAuto rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)]",
        className
      )}
      {...props}
    >
      <table className="wFull borderCollapse text-[var(-FontXs)]">
        <thead>
          <tr className="borderB border-[var(-BorderDefault)]">
            <th className="sticky left0 bg-[var(-SurfaceCard)] px-[var(-SpacingMd)] py-[var(-SpacingSm)] textLeft fontSemibold text-[var(-TextSecondary)]">
              Role / System
            </th>
            {systems.map((sys) => (
              <th
                key={sys}
                className="px-[var(-SpacingMd)] py-[var(-SpacingSm)] textCenter fontSemibold text-[var(-TextSecondary)]"
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
              className="borderB border-[var(-BorderDefault)] last:borderB0 hover:bg-[var(-SurfaceHover)]"
            >
              <td className="sticky left0 bg-[var(-SurfaceCard)] px-[var(-SpacingMd)] py-[var(-SpacingSm)] fontMedium text-[var(-TextPrimary)]">
                {role}
              </td>
              {systems.map((sys) => {
                const perm = permissions[role]?.[sys] ?? "na";
                return (
                  <td key={sys} className="px-[var(-SpacingMd)] py-[var(-SpacingSm)] textCenter">
                    <span
                      className={cn(
                        "inlineFlex h6 w6 itemsCenter justifyCenter rounded-[var(-RadiusSm)] text-[var(-FontXs)] fontBold",
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
