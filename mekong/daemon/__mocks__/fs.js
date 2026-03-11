import { vi } from 'vitest';

const writeFileSync = vi.fn();
const existsSync = vi.fn(() => true);
const readFileSync = vi.fn();
const mkdirSync = vi.fn();
const renameSync = vi.fn();
const appendFileSync = vi.fn();

module.exports = {
    writeFileSync,
    existsSync,
    readFileSync,
    mkdirSync,
    renameSync,
    appendFileSync,
    default: {
        writeFileSync,
        existsSync,
        readFileSync,
        mkdirSync,
        renameSync,
        appendFileSync
    }
};
