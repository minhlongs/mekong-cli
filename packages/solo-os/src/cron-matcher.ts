/**
 * Simple cron expression matcher for pipeline scheduling
 * Supports: '*', specific numbers, and star-slash intervals (e.g. '* /30')
 * Format: 'minute hour dayOfMonth month dayOfWeek'
 */

import type { CronExpression } from './types.js';

/**
 * Parse a single cron field against an actual numeric value.
 * Handles: '*', '5', '1-5', '* /15' (no space in real usage)
 */
function matchField(field: string, value: number): boolean {
  // Wildcard
  if (field === '*') return true;

  // Interval: */n
  if (field.startsWith('*/')) {
    const interval = parseInt(field.slice(2), 10);
    return !isNaN(interval) && interval > 0 && value % interval === 0;
  }

  // Range: 1-5
  if (field.includes('-')) {
    const [start, end] = field.split('-').map(Number);
    return value >= start && value <= end;
  }

  // Comma-separated list: 1,3,5
  if (field.includes(',')) {
    return field.split(',').map(Number).includes(value);
  }

  // Exact number
  const num = parseInt(field, 10);
  return !isNaN(num) && num === value;
}

/**
 * Determine whether a cron schedule should trigger at the given time.
 * Evaluates minute, hour, day-of-month, month, and day-of-week fields.
 */
export function shouldRun(schedule: CronExpression, now: Date): boolean {
  const parts = schedule.trim().split(/\s+/);
  if (parts.length !== 5) return false;

  const [minuteF, hourF, domF, monthF, dowF] = parts;

  const minute = now.getMinutes();
  const hour = now.getHours();
  const dom = now.getDate();
  const month = now.getMonth() + 1; // 1-12
  const dow = now.getDay(); // 0=Sunday

  return (
    matchField(minuteF, minute) &&
    matchField(hourF, hour) &&
    matchField(domF, dom) &&
    matchField(monthF, month) &&
    matchField(dowF, dow)
  );
}
