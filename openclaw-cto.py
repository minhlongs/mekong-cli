#!/usr/bin/env python3
"""OpenClaw CTO — Python daemon. Clean version. Brain + tmux dispatch."""
import asyncio, json, logging, os, subprocess, sys, time, re
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [CTO] %(message)s")
log = logging.getLogger("cto")

SESSION = os.environ.get("CTO_SESSION", "openclaw")
INTERVAL = int(os.environ.get("CTO_INTERVAL", "45"))
PROJECT_ROOT = Path(os.path.expanduser("~/mekong-cli"))
STOP_FILE = Path(os.path.expanduser("~/.openclaw/STOP"))

WORKERS = [
    {"name": "mekong-cli", "dir": ".", "deploy": "pnpm run build"},
    {"name": "algo-trader", "dir": "apps/algo-trader", "deploy": "npx tsc --noEmit"},
    {"name": "well", "dir": "apps/well", "deploy": "npm run build"},
]

def tmux_run(args):
    try:
        return subprocess.run(["tmux"] + args, capture_output=True, text=True, timeout=5).stdout
    except:
        return ""

def capture(pane):
    return tmux_run(["capture-pane", "-t", f"{SESSION}:0.{pane}", "-p", "-S", "-30"])

def is_idle(output):
    tail = "\n".join(output.strip().split("\n")[-5:])
    if "❯" not in tail:
        return False
    if any(x in tail.lower() for x in ["running", "thinking", "tokens"]):
        return False
    low500 = output[-500:].lower()
    if any(x in low500 for x in ["press up to edit", "queued", "pending"]):
        return False
    if "Next:" in output[-300:]:
        return False
    return True

def send_cmd(pane, cmd):
    output = capture(pane)
    if not is_idle(output):
        log.info(f"P{pane}: BUSY — skip")
        return False
    # Sanitize: single line only
    cmd = cmd.split("\n")[0].strip()
    if " /" in cmd and not cmd.startswith("/"):
        cmd = "/" + cmd.lstrip("/ ")
    subprocess.run(["tmux", "send-keys", "-t", f"{SESSION}:0.{pane}", "-l", cmd], timeout=5)
    time.sleep(0.3)
    subprocess.run(["tmux", "send-keys", "-t", f"{SESSION}:0.{pane}", "Enter"], timeout=5)
    log.info(f"P{pane}: SENT {cmd[:80]}")
    return True

def ask_brain(worker):
    try:
        r = subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "scripts" / "cto-brain.py"),
             worker["name"], worker["dir"], worker["deploy"], "0"],
            capture_output=True, text=True, timeout=10, input=""
        )
        cmd = r.stdout.strip().split("\n")[0]
        # Sanitize: remove any second /command
        parts = cmd.split(" /")
        if len(parts) > 1:
            cmd = parts[0]
        return cmd if cmd.startswith("/") else ""
    except:
        return ""

def bootstrap():
    subprocess.run(["tmux", "kill-session", "-t", SESSION], capture_output=True)
    time.sleep(1)
    subprocess.run(["tmux", "new-session", "-d", "-s", SESSION, "-x", "200", "-y", "60"])
    for i in range(1, len(WORKERS)):
        subprocess.run(["tmux", "split-window", "-t", f"{SESSION}:0"])
    subprocess.run(["tmux", "select-layout", "-t", SESSION, "tiled"])
    time.sleep(1)
    for i in range(len(WORKERS)):
        subprocess.run(["tmux", "send-keys", "-t", f"{SESSION}:0.{i}",
                        f"source ~/.zshrc 2>/dev/null && cd {PROJECT_ROOT} && mekong --interactive", "Enter"])
        log.info(f"BOOTSTRAP: P{i} ({WORKERS[i]['name']}) -> mekong --interactive")
    time.sleep(12)
    for i in range(len(WORKERS)):
        out = capture(i)
        if "trust this folder" in out:
            subprocess.run(["tmux", "send-keys", "-t", f"{SESSION}:0.{i}", "Enter"])
    time.sleep(5)
    log.info("BOOTSTRAP: done")

async def main():
    log.info("=" * 50)
    log.info("OpenClaw CTO — Clean Python Daemon")
    log.info(f"Session: {SESSION} | Interval: {INTERVAL}s | Workers: {len(WORKERS)}")
    log.info("=" * 50)

    bootstrap()

    last_dispatch = [0.0] * len(WORKERS)
    last_cmd = [""] * len(WORKERS)
    cycle = 0
    rr_start = 0

    while True:
        cycle += 1
        log.info(f"--- CYCLE {cycle} ---")

        if STOP_FILE.exists():
            log.info("KILLSWITCH ACTIVE")
            await asyncio.sleep(INTERVAL)
            continue

        dispatched = 0
        indices = [(rr_start + j) % len(WORKERS) for j in range(len(WORKERS))]

        for i in indices:
            worker = WORKERS[i]
            pane = i
            output = capture(pane)
            ctx_match = re.findall(r'(\d+)%', output)
            ctx = int(ctx_match[-1]) if ctx_match else 0

            if not is_idle(output):
                log.info(f"P{pane} ({worker['name']}): WORKING [ctx:{ctx}%]")
                # Auto-handle dialogs
                if any(x in output[-200:] for x in ["Enter to select", "Esc to cancel"]):
                    subprocess.run(["tmux", "send-keys", "-t", f"{SESSION}:0.{pane}", "Enter"])
                # Auto-answer push questions
                tail_low = output[-500:].lower()
                if "push" in tail_low and ("remote" in tail_low or "origin" in tail_low) and "?" in tail_low:
                    send_cmd(pane, "Yes, push to origin main")
                    log.info(f"P{pane}: AUTO-ANSWER push")
                continue

            if dispatched >= 1:
                log.info(f"P{pane} ({worker['name']}): IDLE (1-per-cycle)")
                continue

            now = time.time()
            elapsed = now - last_dispatch[i]
            if elapsed < 90:
                log.info(f"P{pane} ({worker['name']}): IDLE (cooldown {int(elapsed)}/90s)")
                continue

            if ctx >= 85:
                send_cmd(pane, "/compact")
                last_dispatch[i] = now
                dispatched += 1
                continue

            log.info(f"P{pane} ({worker['name']}): IDLE -> brain...")
            cmd = ask_brain(worker)

            if cmd:
                cmd_key = cmd.split()[0]
                if last_cmd[i] == cmd_key:
                    rotation = {
                        "/cook": f'/worker-build "Project: {worker["name"]}. Build+test." --fast',
                        "/worker-build": f'/eng-tech-debt "Project: {worker["name"]}. Scan." --fast',
                        "/eng-tech-debt": f'/dev-review "Project: {worker["name"]}. Review." --fast',
                        "/dev-review": f'/worker-test "Project: {worker["name"]}. Test." --fast',
                        "/worker-commit": f'/cto-review "Project: {worker["name"]}. Review." --fast',
                        "/worker-health": f'/cook "Project: {worker["name"]}. Continue." --fast',
                    }
                    cmd = rotation.get(cmd_key, f'/worker-health "Project: {worker["name"]}" --fast')
                    cmd_key = cmd.split()[0]
                    log.info(f"P{pane}: DEDUP rotate -> {cmd_key}")

                log.info(f"BRAIN -> P{pane} ({worker['name']}): {cmd[:80]}")
                if send_cmd(pane, cmd):
                    last_dispatch[i] = now
                    last_cmd[i] = cmd_key
                    dispatched += 1
                    log.info(f"DELEGATED P{pane} ({worker['name']}) -> {cmd_key}")
            else:
                log.info(f"P{pane} ({worker['name']}): brain empty")
                last_dispatch[i] = now

        rr_start = (rr_start + 1) % len(WORKERS)
        await asyncio.sleep(INTERVAL)

if __name__ == "__main__":
    asyncio.run(main())
