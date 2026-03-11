import { cn } from '@/lib/utils';
import type { MissionStatus } from '@/lib/api-client';

const STATUS_STYLES: Record<MissionStatus, string> = {
  queued: 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20',
  running: 'bg-blue-500/10 text-blue-500 border-blue-500/20',
  completed: 'bg-green-500/10 text-green-500 border-green-500/20',
  failed: 'bg-destructive/10 text-destructive border-destructive/20',
  cancelled: 'bg-muted text-muted-foreground border-border',
};

const STATUS_DOTS: Record<MissionStatus, string> = {
  queued: 'bg-yellow-500',
  running: 'bg-blue-500 animate-pulse',
  completed: 'bg-green-500',
  failed: 'bg-destructive',
  cancelled: 'bg-muted-foreground',
};

interface MissionStatusBadgeProps {
  status: MissionStatus;
}

export function MissionStatusBadge({ status }: MissionStatusBadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium border',
        STATUS_STYLES[status],
      )}
    >
      <span className={cn('h-1.5 w-1.5 rounded-full', STATUS_DOTS[status])} />
      {status}
    </span>
  );
}
