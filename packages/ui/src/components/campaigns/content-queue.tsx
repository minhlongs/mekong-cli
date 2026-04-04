"use client";
import * as React from "react";
import { cn } from "../../lib/utils";
export interface ContentItem { title: string; type: string; status: "draft" | "review" | "scheduled" | "published"; date: string; }
export interface ContentQueueProps extends React.HTMLAttributes<HTMLDivElement> { items: ContentItem[]; }
const statusColor = { draft: "var(--status-idle)", review: "var(--status-warning)", scheduled: "var(--accent-teal-500)", published: "var(--status-healthy)" };
const ContentQueue = React.forwardRef<HTMLDivElement, ContentQueueProps>(({ className, items, ...props }, ref) => (
  <div ref={ref} className={cn("rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--surface-card)] overflow-hidden", className)} {...props}>
    <div className="border-b border-[var(--border-default)] px-[var(--spacing-lg)] py-[var(--spacing-sm)]"><span className="text-[var(--font-sm)] font-semibold text-[var(--text-primary)]">Content Queue</span></div>
    {items.map((item, i) => (<div key={i} className="flex items-center gap-[var(--spacing-md)] border-b border-[var(--border-default)] px-[var(--spacing-lg)] py-[var(--spacing-sm)] last:border-b-0"><span className="h-2 w-2 rounded-full" style={{ backgroundColor: statusColor[item.status] }} /><span className="flex-1 text-[var(--font-sm)] text-[var(--text-primary)]">{item.title}</span><span className="text-[var(--font-xs)] text-[var(--text-muted)]">{item.type}</span><span className="text-[var(--font-xs)] text-[var(--text-muted)]">{item.date}</span></div>))}
  </div>
));
ContentQueue.displayName = "ContentQueue";
export { ContentQueue };
