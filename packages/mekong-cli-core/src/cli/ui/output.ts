import chalk from 'chalk';

// ─── Claude Code Color Palette ──────────────────────────────────────
const C = {
  border:     '#d0d7de',      // subtle gray — thin borders (like GitHub's UI)
  accent:     '#58a6ff',      // soft blue for links/important text
  success:    '#3fb950',      // green — GO / HEALTHY
  warning:    '#d29922',      // amber — CAUTION
  error:      '#f85149',      // red — ABORT / CRITICAL
  info:       '#58a6ff',      // blue for info
  muted:      '#8b949e',      // secondary gray text
  heading:    '#f0f6fc',      // primary white text
};

// ─── Helpers ────────────────────────────────────────────────────────
const W = process.stdout.columns || 90;

/** Center a string within width w */
function center(s: string, w: number): string {
  const pad = Math.max(0, (w - s.length) / 2);
  return ' '.repeat(pad) + s;
}

// ─── Claude Code–style UI System ────────────────────────────────────

/** Clean title header — thin top/bottom border, no background panel */
export function missionHeader(title: string, subtitle?: string): void {
  console.log('');
  const w = W - 2;

   // Top thin border
  console.log(chalk.hex(C.border).dim('\u2500'.repeat(w)));

   // Title row — centered, no background
  if (subtitle) {
    const combined = `${title}    ${subtitle}`;
    const line = center(combined, w);
    console.log(chalk.bold.white(line));
   } else {
    const line = center(title, w);
    console.log(chalk.bold.white(line));
   }

   // Bottom thin border
  console.log(chalk.hex(C.border).dim('\u2500'.repeat(w)));
}

/** Open a bordered panel with title — thin lines, no background fill */
export function panel(title: string, opts?: { width?: number }): void {
  const w = (opts?.width || W - 4);

   // Top border + title on same line
  console.log(chalk.hex(C.border).dim('\u2500'.repeat(w)));
  const label = ` ${title} `;
  const line = center(label, w);
  console.log(line);

   // Separator — thin dashed line
  console.log(chalk.hex(C.border).dim('\u2500'.repeat(w)));
}

/** Close a panel */
export function panelClose(): void {
  const w = W - 4;
  console.log(chalk.hex(C.border).dim('\u2500'.repeat(w)));
}

/** Status badge: GO / NO-GO / CAUTION / STANDBY — compact dot + label */
export function statusBadge(status: 'GO' | 'NO-GO' | 'CAUTION' | 'STANDBY'): void {
  let color = C.success;

  if (status === 'NO-GO')             { color = C.error;    }
  if (status === 'CAUTION')           { color = C.warning; }
  if (status === 'STANDBY')          { color = C.info;     }

  const dot = '\u25cf';
  console.log(`${chalk.bold.hex(color)(dot)} ${chalk.bold.hex(color)(status)}`);
}

/** KV row inside a panel — clean left-aligned */
export function kv(key: string, value: string): void {
  console.log(`   ${chalk.gray(key + ':')} ${chalk.hex(C.accent).bold(value)}`);
}

/** KV with colored value */
export function kvColor(key: string, value: string, color: string): void {
  console.log(`   ${chalk.gray(key + ':')} ${chalk.bold.hex(color)(value)}`);
}

/** Telemetry bar — simple progress indicator */
export function telemetryBar(label: string, pct: number, maxPct?: number): void {
  const p = Math.min(100, Math.max(0, pct));
  const m = maxPct || 100;
  const filled = Math.round((p / m) * 30);
  const empty = 30 - filled;

  let barColor = C.success;
  if (p > 80) barColor = C.warning;
  if (p > 95) barColor = C.error;

  const bar = '█'.repeat(filled) + '░'.repeat(empty);
  console.log(`   ${chalk.gray(label.padEnd(14))} [${chalk.bold.hex(barColor)(bar)}] ${chalk.white(String(p).padStart(3) + "%")}`);
}

/** Divider line — thin, subtle */
export function hRule(): void {
  const w = W - 4;
  console.log(chalk.hex(C.border).dim('\u2500'.repeat(w)));
}

/** Section header inside panel — bold text with thin underline */
export function section(title: string): void {
  console.log('');
  console.log(chalk.bold.white(title));
  const w = W - 6;
  console.log(chalk.hex(C.border).dim('\u2500'.repeat(Math.min(w, title.length + 4))));
}

/** Table header row — clean columns */
export function tableHeader(cols: string[]): void {
  const sep = ' │ ';
  console.log(`   ${cols.map(c => chalk.bold.white(c.padEnd(16))).join(sep)}`);
  console.log(`   ${chalk.hex(C.border).dim('\u2500'.repeat(18 * cols.length + 4 * (cols.length - 1)))}`);
}

/** Table data row — clean columns */
export function tableRow(cells: string[], color?: string): void {
  const c = color ? chalk.hex(color) : chalk.white;
  console.log(`   ${cells.map(cell => c(cell.padEnd(16))).join(chalk.hex(C.border).dim(' │ '))}`);
}

/** Status indicator dot + text — compact */
export function statusDot(status: 'green' | 'amber' | 'red' | 'cyan', label: string): void {
  const map = { green: C.success, amber: C.warning, red: C.error, cyan: C.info };
  console.log(`   ${chalk.bold.hex(map[status])}\u25cf ${label}`);
}

// ─── Legacy compat (backward-compatible with all existing imports) ──

/** Heading — clean title with thin borders */
export function heading(text: string): void {
  const w = W - 4;
  console.log('');
  console.log(chalk.hex(C.border).dim('\u2500'.repeat(w)));
  const line = center(text, w);
  console.log(line);
  console.log(chalk.hex(C.border).dim('\u2500'.repeat(w)));
}

/** Success — clean single-line output with green accent */
export function success(text: string): void {
  console.log('');
  const dot = String.fromCodePoint(0x2713); // ✓
  console.log(`   ${chalk.bold.hex(C.success)(dot)} ${chalk.bold.white(text)}`);
}

/** Error — clean single-line output with red accent */
export function error(text: string): void {
  const w = W - 4;
  process.stderr.write(''); // flush stdout first
  console.log('');
  const cross = String.fromCodePoint(0x2717); // ✗
  console.error(`   ${chalk.bold.hex(C.error)(cross)} ${chalk.bold.white(text)}`);
}

/** Warn — clean single-line output with amber accent */
export function warn(text: string): void {
  console.log('');
  const warnSym = String.fromCodePoint(0x26a0); // ⚠
  console.log(`   ${chalk.bold.hex(C.warning)(warnSym)} ${chalk.bold.white(text)}`);
}

/** Info — clean single-line output with blue accent */
export function info(text: string): void {
  console.log('');
  const infoSym = String.fromCodePoint(0x2139); // ℹ
  console.log(`   ${chalk.bold.hex(C.info)(infoSym)} ${chalk.white(text)}`);
}

/** KeyValue — clean left-aligned key-value */
export function keyValue(key: string, value: string): void {
  console.log(`   ${chalk.gray(key + ':')} ${chalk.hex(C.accent).bold(value)}`);
}

/** Divider — thin subtle line */
export function divider(): void {
  const w = W - 4;
  console.log(chalk.hex(C.border).dim('\u2500'.repeat(w)));
}
