// Source excerpt: /Users/macbook/mekong-cli/packages/ui/src/components/care/ticket-card.tsx
// Bundled in _ds_bundle.js as window.TicketCard

"use client";
import * as React from "react";
import { cn } from "../../lib/utils";
export interface TicketCardProps extends React.HTMLAttributes<HTMLDivElement> { label?: string; }
const TicketCard = React.forwardRef<HTMLDivElement, TicketCardProps>(({ className, label, ...props }, ref) => (
  <div ref={ref} className={cn("rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] p-[var(-SpacingLg)]", className)} {...props}>
    <div className="text-[var(-FontSm)] fontSemibold text-[var(-TextPrimary)]">Ticket</div>
    <div className="mt-[var(-SpacingSm)] text-[var(-FontXs)] text-[var(-TextMuted)]">{label || "Component ready"}</div>
  </div>
));
TicketCard.displayName = "TicketCard";
export { TicketCard };
