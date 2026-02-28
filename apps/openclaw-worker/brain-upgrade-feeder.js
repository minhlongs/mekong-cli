#!/usr/bin/env node
/**
 * 🧬 Brain Upgrade Auto-Feeder
 * 
 * Extracts 21 individual sub-tasks from 7 batch files
 * and drops them into /tasks/ in phased batches (4 at a time).
 * 
 * Waits for queue to drain before dropping next batch.
 * Thermal-aware: pauses if system is overheated.
 * 
 * Usage: node brain-upgrade-feeder.js
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const TASKS_DIR = '/Users/macbookprom1/mekong-cli/tasks';
const PROCESSED_DIR = path.join(TASKS_DIR, 'processed');
const BATCH_SIZE = 2; // Drop 2 at a time (match 2 workers)
const POLL_MS = 30000; // Check queue every 30s
const PHASE_DELAY_MS = 60000; // 60s between phases for cooling

function log(msg) {
    const ts = new Date().toLocaleTimeString('en-GB');
    const line = `[${ts}] [feeder] ${msg}`;
    console.log(line);
    try {
        fs.appendFileSync('/Users/macbookprom1/tom_hum_cto.log', line + '\n');
    } catch { }
}

function getTasksInQueue() {
    try {
        return fs.readdirSync(TASKS_DIR)
            .filter(f => /^(CRITICAL_|HIGH_|MEDIUM_|LOW_).*\.txt$/.test(f));
    } catch { return []; }
}

function extractSubTasks() {
    const batchFiles = [];
    for (let i = 1; i <= 7; i++) {
        const f = path.join(PROCESSED_DIR, `CRITICAL_brain_upgrade_batch_${i}_1771431979.txt`);
        if (fs.existsSync(f)) batchFiles.push(f);
    }

    const tasks = [];
    for (const batchFile of batchFiles) {
        const content = fs.readFileSync(batchFile, 'utf-8');
        // Split by ========== [Task N: ... ] ==========
        const parts = content.split(/==========\s*\[Task \d+:\s*([^\]]+)\]\s*==========/);
        // parts: [header, name1, content1, name2, content2, ...]
        for (let i = 1; i < parts.length; i += 2) {
            const name = parts[i].trim().replace('.txt', '');
            const taskContent = parts[i + 1] ? parts[i + 1].trim() : '';
            if (taskContent) {
                // Add PROJECT header + SCOPE LOCK — NEVER touch other projects!
                const prefix = `PROJECT: /Users/macbookprom1/mekong-cli/apps/openclaw-worker\n\n🔒 SCOPE LOCK — ĐỌC KỸ TRƯỚC KHI LÀM:\n- CHỈ ĐƯỢC sửa files trong apps/openclaw-worker/\n- CẤM TUYỆT ĐỐI đụng vào apps/anima119, apps/84tea, apps/wellnexus, apps/apex-os, apps/sophia-*, apps/agencyos-*, apps/raas-*\n- CẤM fix build failures của projects khác\n- Nếu build RED do project khác → BỎ QUA, chỉ focus openclaw-worker\n- Vi phạm scope = PHẢN QUÂN\n\n`;
                tasks.push({
                    name,
                    content: prefix + taskContent,
                    priority: name.startsWith('HIGH') ? 'HIGH' : 'MEDIUM'
                });
            }
        }
    }
    return tasks;
}

function dropTask(task) {
    const filename = `${task.priority}_brain_${task.name.replace(/^(HIGH_|MEDIUM_)/, '')}_recovery.txt`;
    const filepath = path.join(TASKS_DIR, filename);
    const processedPath = path.join(PROCESSED_DIR, filename);

    // Clean stale processed copy if exists
    if (fs.existsSync(processedPath)) {
        fs.unlinkSync(processedPath);
    }

    fs.writeFileSync(filepath, task.content);
    log(`📥 DROPPED: ${filename} (${task.content.length} bytes)`);
    return filename;
}

function getLoadAvg() {
    try {
        const out = execSync('sysctl -n vm.loadavg', { encoding: 'utf-8' });
        const match = out.match(/[\d.]+/);
        return match ? parseFloat(match[0]) : 0;
    } catch { return 0; }
}

async function sleep(ms) {
    return new Promise(r => setTimeout(r, ms));
}

async function main() {
    log('🧬 Brain Upgrade Auto-Feeder STARTED');

    const allTasks = extractSubTasks();
    log(`📋 Extracted ${allTasks.length} individual tasks from 7 batch files`);

    if (allTasks.length === 0) {
        log('❌ No tasks extracted! Check batch files in processed/');
        process.exit(1);
    }

    // Log all tasks
    allTasks.forEach((t, i) => log(`  ${i + 1}. ${t.priority}_${t.name}`));

    let dropped = 0;
    let phase = 0;

    while (dropped < allTasks.length) {
        phase++;

        // Wait for queue to have room
        let queueCount = getTasksInQueue().length;
        while (queueCount >= BATCH_SIZE) {
            log(`⏳ Queue has ${queueCount} tasks, waiting for room...`);
            await sleep(POLL_MS);
            queueCount = getTasksInQueue().length;
        }

        // Check thermal
        const load = getLoadAvg();
        if (load > 25) {
            log(`🌡️ Load ${load} > 25 — waiting for cooldown...`);
            await sleep(PHASE_DELAY_MS);
            continue;
        }

        // Drop next batch
        const batchEnd = Math.min(dropped + BATCH_SIZE, allTasks.length);
        log(`\n📦 Phase ${phase}: Dropping tasks ${dropped + 1}-${batchEnd} of ${allTasks.length}`);

        for (let i = dropped; i < batchEnd; i++) {
            dropTask(allTasks[i]);
        }
        dropped = batchEnd;

        log(`✅ Phase ${phase} complete — ${dropped}/${allTasks.length} dropped (${allTasks.length - dropped} remaining)`);

        // Wait between phases for processing
        if (dropped < allTasks.length) {
            log(`⏱️ Waiting ${PHASE_DELAY_MS / 1000}s for processing before next phase...`);
            await sleep(PHASE_DELAY_MS);
        }
    }

    log(`\n🎉 ALL ${allTasks.length} TASKS DROPPED! Feeder complete.`);
    log(`CTO will process them sequentially via P0 CHÍNH.`);
    log(`Expected completion: ~${Math.ceil(allTasks.length * 10 / 60)} hours`);
}

main().catch(e => {
    log(`❌ FEEDER ERROR: ${e.message}`);
    process.exit(1);
});
