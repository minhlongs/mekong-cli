import chalk from 'chalk';

export function heading(text: string): void {
  console.log(chalk.bold.cyan(`\n${text}\n`));
}

export function success(text: string): void {
  console.log(chalk.green(`✓ ${text}`));
}

export function error(text: string): void {
  console.error(chalk.red(`✗ ${text}`));
}

export function warn(text: string): void {
  console.log(chalk.yellow(`⚠ ${text}`));
}

export function info(text: string): void {
  console.log(chalk.blue(`ℹ ${text}`));
}

export function keyValue(key: string, value: string): void {
  console.log(`  ${chalk.gray(key + ':')} ${value}`);
}

export function divider(): void {
  console.log(chalk.gray('─'.repeat(50)));
}
