"use client";

import * as React from "react";
import { cn } from "../../lib/utils";

export interface BoardCardProps extends React.HTMLAttributes<HTMLDivElement> {
  title: string;
  date: string;
  attendees: number;
  materialsReady: boolean;
  actionItems: number;
}

const BoardCard = React.forwardRef<HTMLDivElement, BoardCardProps>(
  ({ className, title, date, attendees, materialsReady, actionItems, ...props }, ref) => (
    <div ref={ref} className={cn("flex flexCol gap-[var(-SpacingSm)] rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] p-[var(-SpacingLg)]", className)} {...props}>
      <div className="flex itemsCenter justifyBetween">
        <span className="text-[var(-FontMd)] fontSemibold text-[var(-TextPrimary)]">{title}</span>
        <span className="text-[var(-FontXs)] text-[var(-TextMuted)]">{date}</span>
      </div>
      <div className="flex itemsCenter gap-[var(-SpacingLg)] text-[var(-FontXs)]">
        <span className="text-[var(-TextSecondary)]">{attendees} attendees</span>
        <span className={materialsReady ? "text-[var(-StatusHealthy)]" : "text-[var(-StatusWarning)]"}>
          Materials: {materialsReady ? "Ready" : "Pending"}
        </span>
        <span className="text-[var(-TextSecondary)]">{actionItems} action items</span>
      </div>
    </div>
  )
);
BoardCard.displayName = "BoardCard";
export { BoardCard };
