"use client";
import * as React from "react";
import { cn } from "../../lib/utils";
export interface ContentItem { title: string; type: string; status: "draft" | "review" | "scheduled" | "published"; date: string; }
export interface ContentQueueProps extends React.HTMLAttributes<HTMLDivElement> { items: ContentItem[]; }
const statusColor = { draft: "var(-StatusIdle)", review: "var(-StatusWarning)", scheduled: "var(-AccentTeal500)", published: "var(-StatusHealthy)" };
const ContentQueue = React.forwardRef<HTMLDivElement, ContentQueueProps>(({ className, items, ...props }, ref) => (
  <div ref={ref} className={cn("rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] overflowHidden", className)} {...props}>
    <div className="borderB border-[var(-BorderDefault)] px-[var(-SpacingLg)] py-[var(-SpacingSm)]"><span className="text-[var(-FontSm)] fontSemibold text-[var(-TextPrimary)]">Content Queue</span></div>
    {items.map((item, i) => (<div key={i} className="flex itemsCenter gap-[var(-SpacingMd)] borderB border-[var(-BorderDefault)] px-[var(-SpacingLg)] py-[var(-SpacingSm)] last:borderB0"><span className="h2 w2 roundedFull" style={{ backgroundColor: statusColor[item.status] }} /><span className="flex1 text-[var(-FontSm)] text-[var(-TextPrimary)]">{item.title}</span><span className="text-[var(-FontXs)] text-[var(-TextMuted)]">{item.type}</span><span className="text-[var(-FontXs)] text-[var(-TextMuted)]">{item.date}</span></div>))}
  </div>
));
ContentQueue.displayName = "ContentQueue";
export { ContentQueue };
