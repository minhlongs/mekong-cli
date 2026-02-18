import { vi } from 'vitest';
import { EventEmitter } from 'events';

const spawn = vi.fn((cmd, args, opts) => {
    const child = new EventEmitter();
    child.stdout = new EventEmitter();
    child.stderr = new EventEmitter();
    child.kill = vi.fn();
    process.nextTick(() => {
        child.emit('close', 0);
    });
    return child;
});

const execSync = vi.fn(() => '');

const exec = vi.fn();
const fork = vi.fn();

module.exports = {
    spawn,
    execSync,
    exec,
    fork,
    default: {
        spawn,
        execSync,
        exec,
        fork
    }
};
