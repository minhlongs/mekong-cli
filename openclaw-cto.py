#!/usr/bin/env python3
"""
OpenClaw CTO v2 — Python daemon with native OpenClaw architecture.
Integrates: WorkerPool + TaskRouter + Dispatcher + Jidoka.
Execution layer: tmux send-keys (unchanged, proven).
Brain: cto-brain.py (Ollama → bash fallback).
"""
import asyncio
import logging
import os
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.daemon.dispatcher import Dispatcher, LoadBalanceStrategy
from src.daemon.jidoka import JidokaMonitor
from src.daemon.task_router import TaskRouter, TaskPriority
from src.daemon.worker_pool import WorkerPool, WorkerInfo, WorkerState

logging.basicConfig(level=logging.INFO, format="%(asctime)s [CTO] %(message)s")
log = logging.getLogger("cto")

# Config
SESSION = os.environ.get("CTO_SESSION", "openclaw")
INTERVAL = int(os.environ.get("CTO_INTERVAL", "45"))
PROJECT_ROOT = Path(os.environ.get("PROJECT_ROOT", os.path.expanduser("~/mekong-cli")))
STOP_FILE = Path(os.path.expanduser("~/.openclaw/STOP"))

# Worker definitions — capability maps to tmux pane
WORKER_DEFS = [
    {"name": "mekong-cli",   "pane": 0, "dir": ".",                       "deploy": "pnpm run build",    "capability": "builder"},
    {"name": "algo-trader",  "pane": 1, "dir": "apps/algo-trader",        "deploy": "npx tsc --noEmit",  "capability": "tester"},
    {"name": "well",         "pane": 2, "dir": "apps/well",               "deploy": "npm run build",     "capability": "reviewer"},
    {"name": "raas-landing", "pane": 5, "dir": "apps/raas-landing",       "deploy": "npm run build",     "capability": "builder"},
    {"name": "sophia-factory","pane": 6, "dir": "apps/sophia-factory",    "deploy": "npm run build",     "capability": "builder"},
    {"name": "saas-dashboard","pane": 7, "dir": "apps/saas-dashboard",    "deploy": "npx tsc --noEmit",  "capability": "tester"},
]

# --- TMUX EXECUTION LAYER (proven, unchanged) ---
def tmux_cmd(cmd: str) -> str:
    try:
        return subprocess.run(["tmux"] + cmd.split(), capture_output=True, text=True, timeout=5).stdout
    except Exception:
        return ""

def capture_pane(pane: int) -> str:
    return tmux_cmd(f"capture-pane -t {SESSION}:0.{pane} -p -S -30")

def send_to_pane(pane: int, cmd: str) -> bool:
    output = capture_pane(pane)
    if not is_idle(output):
        log.info(f"P{pane}: BUSY — skip")
        return False
    subprocess.run(["tmux", "send-keys", "-t", f"{SESSION}:0.{pane}", "-l", cmd], timeout=5)
    time.sleep(0.3)
    subprocess.run(["tmux", "send-keys", "-t", f"{SESSION}:0.{pane}", "Enter"], timeout=5)
    log.info(f"P{pane}: SENT {cmd[:80]}")
    return True

def is_idle(output: str) -> bool:
    tail = "\n".join(output.strip().split("\n")[-5:])
    if "❯" not in tail:
        return False
    if any(x in tail.lower() for x in ["running", "thinking", "tokens"]):
        return False
    if "pending" in output[-500:].lower() or "open)" in output[-500:].lower():
        return False
    if "Next:" in output[-300:] or "○ Next:" in output[-300:]:
        return False
    if any(x in output[-500:].lower() for x in ["press up to edit", "queued"]):
        return False
    return True

def get_ctx(output: str) -> int:
    import re
    m = re.findall(r'(\d+)%', output)
    return int(m[-1]) if m else 0

# --- BRAIN ---
def ask_brain(worker: dict) -> str:
    try:
        return subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "scripts" / "cto-brain.py"),
             worker["name"], worker["dir"], worker["deploy"], "0"],
            capture_output=True, text=True, timeout=10, input=""
        ).stdout.strip()
    except Exception:
        return ""

# --- BOOTSTRAP ---
def bootstrap():
    subprocess.run(["tmux", "kill-session", "-t", SESSION], capture_output=True)
    time.sleep(1)
    subprocess.run(["tmux", "new-session", "-d", "-s", SESSION, "-x", "200", "-y", "60"])
    for i in range(1, len(WORKER_DEFS)):
        subprocess.run(["tmux", "split-window", "-t", f"{SESSION}:0"])
    subprocess.run(["tmux", "select-layout", "-t", SESSION, "tiled"])
    time.sleep(1)
    for w in WORKER_DEFS:
        subprocess.run(["tmux", "send-keys", "-t", f"{SESSION}:0.{w['pane']}",
                        f"source ~/.zshrc 2>/dev/null && cd {PROJECT_ROOT} && mekong --interactive", "Enter"])
        log.info(f"BOOTSTRAP: P{w['pane']} ({w['name']}) → mekong --interactive")
    time.sleep(12)
    for w in WORKER_DEFS:
        output = capture_pane(w["pane"])
        if "trust this folder" in output:
            subprocess.run(["tmux", "send-keys", "-t", f"{SESSION}:0.{w['pane']}", "Enter"])
    time.sleep(5)
    log.info("BOOTSTRAP: done")

# --- NATIVE MODULES SETUP ---
def build_native_infra() -> tuple[WorkerPool, TaskRouter, Dispatcher, JidokaMonitor]:
    """Register all workers into WorkerPool, wire up Dispatcher + Jidoka."""
    pool = WorkerPool()
    router = TaskRouter()
    jidoka = JidokaMonitor()

    # Register tmux pane workers into WorkerPool (no PM2 spawn — tmux IS the worker)
    for w in WORKER_DEFS:
        pool.workers[w["name"]] = WorkerInfo(
            id=w["name"],
            name=w["name"],
            capability=w["capability"],
            state=WorkerState.IDLE,
        )
        log.info(f"POOL: Registered {w['name']} (cap={w['capability']})")

    dispatcher = Dispatcher(
        worker_pool=pool,
        task_router=router,
        strategy=LoadBalanceStrategy.ROUND_ROBIN,
    )
    return pool, router, dispatcher, jidoka

# --- JIDOKA VERIFY ---
def jidoka_check(jidoka: JidokaMonitor, pool: WorkerPool, worker_def: dict, pane_output: str) -> None:
    """Run Jidoka error detection on pane output. Mark worker state on error."""
    pattern = jidoka.detect_error(pane_output)
    if pattern:
        action = jidoka.handle_error(worker_id=worker_def["name"], error=pane_output[-500:], pattern=pattern)
        log.warning(f"JIDOKA P{worker_def['pane']} ({worker_def['name']}): [{pattern.name}] → {action}")
        # Reflect error state in pool
        if pattern.severity.value in ("high", "critical"):
            pool.mark_failed(worker_def["name"])

# --- MAIN ---
async def main():
    log.info("=" * 55)
    log.info("OpenClaw CTO v2 — Native Modules + Jidoka + tmux")
    log.info(f"Session: {SESSION} | Interval: {INTERVAL}s | Workers: {len(WORKER_DEFS)}")
    log.info("=" * 55)

    bootstrap()
    pool, router, dispatcher, jidoka = build_native_infra()

    last_dispatch = {w["name"]: 0.0 for w in WORKER_DEFS}
    last_cmd     = {w["name"]: "" for w in WORKER_DEFS}
    cycle = 0

    while True:
        cycle += 1
        log.info(f"--- CYCLE {cycle} ---")

        # Kill switch
        if STOP_FILE.exists():
            log.info("KILLSWITCH ACTIVE — pausing")
            await asyncio.sleep(INTERVAL)
            continue

        # Log stats from native modules every 5 cycles
        if cycle % 5 == 0:
            stats = dispatcher.get_stats()
            log.info(f"STATS: pool={stats['workers']} queue={stats['queue']}")

        dispatched = 0
        # Round-robin via pool state — iterate panes in cyclic order
        ordered = sorted(WORKER_DEFS, key=lambda w: last_dispatch[w["name"]])

        for wdef in ordered:
            pane = wdef["pane"]
            output = capture_pane(pane)
            ctx = get_ctx(output)

            # Jidoka check on every captured pane
            jidoka_check(jidoka, pool, wdef, output)

            worker_info = pool.workers.get(wdef["name"])
            if not is_idle(output):
                log.info(f"P{pane} ({wdef['name']}): WORKING [ctx:{ctx}%]")
                # Mark busy in pool if not already
                if worker_info and worker_info.state != WorkerState.BUSY:
                    pool.mark_busy(wdef["name"])
                # Auto-handle dialogs
                if any(x in output[-200:] for x in ["Enter to select", "Esc to cancel"]):
                    subprocess.run(["tmux", "send-keys", "-t", f"{SESSION}:0.{pane}", "Enter"])
                # Auto-answer worker questions (push, confirm, y/n)
                tail500 = output[-500:].lower()
                if "push" in tail500 and ("remote" in tail500 or "origin" in tail500):
                    send_to_pane(pane, "Yes, push to origin main")
                    log.info(f"P{pane}: AUTO-ANSWER push yes")
                elif any(x in tail500 for x in ["y/n", "proceed?", "continue?", "confirm?"]):
                    send_to_pane(pane, "yes")
                    log.info(f"P{pane}: AUTO-ANSWER yes")
                continue

            # Worker is idle — sync pool state
            if worker_info and worker_info.state == WorkerState.BUSY:
                pool.mark_idle(wdef["name"])
                # Complete any active task for this worker in router
                active = [t for t in router._active_tasks.values() if t.assigned_to == wdef["name"]]
                for t in active:
                    dispatcher.complete_task(t.task_id)

            if dispatched >= 1:
                log.info(f"P{pane} ({wdef['name']}): IDLE (1-per-cycle limit)")
                continue

            # Cooldown: skip if dispatched too recently
            now = time.time()
            elapsed = now - last_dispatch[wdef["name"]]
            if elapsed < 90:
                log.info(f"P{pane} ({wdef['name']}): cooldown {int(elapsed)}/90s")
                continue

            # Context >= 85% → compact
            if ctx >= 85:
                send_to_pane(pane, "/compact")
                last_dispatch[wdef["name"]] = now
                dispatched += 1
                # Enqueue compact task in router for tracking
                router.enqueue(f"compact ctx {wdef['name']}", priority="HIGH", capability=wdef["capability"])
                continue

            # Use Dispatcher to select worker (respects capability + strategy)
            result = dispatcher.dispatch(
                description=f"brain-task:{wdef['name']}",
                priority="MEDIUM",
                capability=wdef["capability"],
            )

            if not result.success:
                log.info(f"P{pane} ({wdef['name']}): dispatcher skip ({result.error})")
                # Still ask brain even if dispatcher didn't formally assign
            
            # Ask brain for command
            log.info(f"P{pane} ({wdef['name']}): IDLE → brain...")
            cmd = ask_brain(wdef)

            # Complete the dispatcher task immediately (brain gave us the cmd)
            if result.success and result.task_id:
                dispatcher.complete_task(result.task_id)

            if cmd:
                cmd_key = cmd.split()[0] if cmd else ""
                # Dedup rotation
                if last_cmd[wdef["name"]] == cmd_key:
                    rotation = {
                        "/cook":            f'/worker-build "Project: {wdef["name"]}. Build+test. {wdef["deploy"]}" --fast',
                        "/worker-build":    f'/eng-tech-debt "Project: {wdef["name"]}. Scan tech debt." --fast',
                        "/eng-tech-debt":   f'/dev-review "Project: {wdef["name"]}. Code review." --fast',
                        "/dev-review":      f'/worker-test "Project: {wdef["name"]}. Run tests." --fast',
                    }
                    cmd = rotation.get(cmd_key, f'/worker-health "Project: {wdef["name"]}" --fast')
                    cmd_key = cmd.split()[0]
                    log.info(f"P{pane}: DEDUP rotate → {cmd_key}")

                # Enqueue as HIGH task in router for audit trail
                task = router.enqueue(cmd[:100], priority="HIGH", capability=wdef["capability"])

                log.info(f"BRAIN → P{pane} ({wdef['name']}): {cmd[:80]}")
                if send_to_pane(pane, cmd):
                    pool.mark_busy(wdef["name"])
                    task.assigned_to = wdef["name"]
                    last_dispatch[wdef["name"]] = now
                    last_cmd[wdef["name"]] = cmd_key
                    dispatched += 1
                    log.info(f"DELEGATED P{pane} ({wdef['name']}) → {cmd_key}")
                else:
                    # Pane went busy between check and send — fail the task
                    router.fail(task.task_id, "pane busy at send time")
                    pool.mark_idle(wdef["name"])
            else:
                log.info(f"P{pane} ({wdef['name']}): brain empty — skip")
                last_dispatch[wdef["name"]] = now
                if result.success and result.task_id:
                    pass  # already completed above

        await asyncio.sleep(INTERVAL)

if __name__ == "__main__":
    asyncio.run(main())
