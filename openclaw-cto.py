#!/usr/bin/env python3
"""OpenClaw CTO v7.1 — enforce worker dirs + all previous fixes."""
import asyncio, json, logging, os, subprocess, sys, time, re
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [CTO] %(message)s")
log = logging.getLogger("cto")

SESSION = os.environ.get("CTO_SESSION", "openclaw")
INTERVAL = int(os.environ.get("CTO_INTERVAL", "20"))
PROJECT_ROOT = Path(os.path.expanduser("~/mekong-cli"))
STOP_FILE = Path(os.path.expanduser("~/.openclaw/STOP"))
NO_BOOTSTRAP = "--no-bootstrap" in sys.argv

# WORKERS: each has assigned dir — CTO enforces this
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

def get_actual_dir(output):
    """Extract actual working directory from CC CLI status bar."""
    match = re.findall(r'\U0001F4C1\s+(~?/[^\s]+)', output)
    if match:
        d = match[-1].replace("~", os.path.expanduser("~"))
        try:
            return str(Path(d).relative_to(PROJECT_ROOT))
        except ValueError:
            return d
    return "."

def is_idle(output):
    tail = "\n".join(output.strip().split("\n")[-5:])
    if "\u276f" not in tail:
        return False
    if any(x in tail.lower() for x in ["running", "thinking", "tokens"]):
        return False
    low500 = output[-500:].lower()
    if any(x in low500 for x in ["press up to edit", "queued", "pending"]):
        return False
    if "Next:" in output[-300:]:
        return False
    return True

def has_question(output):
    """Only answer if real question in last 8 lines."""
    if not is_idle(output):
        return False, ""
    lines8 = output.strip().split("\n")[-8:]
    tail_text = "\n".join(lines8).lower()
    if "?" not in tail_text:
        return False, ""
    if "unresolved" in tail_text:
        return False, ""
    if "push" in tail_text and ("remote" in tail_text or "origin" in tail_text):
        return True, "push"
    question_markers = ["do you want", "shall i", "should i", "proceed", "confirm",
                       "approve", "continue", "y/n", "yes/no"]
    if any(m in tail_text for m in question_markers):
        return True, "confirm"
    return False, ""

def send_cmd(pane, cmd):
    try:
        output = capture(pane)
        if not is_idle(output):
            log.info(f"P{pane}: BUSY — skip")
            return False
        cmd = cmd.split("\n")[0].strip()
        if " /" in cmd and not cmd.startswith("/"):
            cmd = "/" + cmd.lstrip("/ ")
        subprocess.run(["tmux", "send-keys", "-t", f"{SESSION}:0.{pane}", "-l", cmd], timeout=8)
        time.sleep(0.3)
        subprocess.run(["tmux", "send-keys", "-t", f"{SESSION}:0.{pane}", "Enter"], timeout=5)
        log.info(f"P{pane}: SENT {cmd[:80]}")
        return True
    except Exception as e:
        log.warning(f"P{pane}: send_cmd FAILED: {e}")
        return False

def ask_brain(worker, ctx):
    try:
        r = subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "scripts" / "cto-brain.py"),
             worker["name"], worker["dir"], worker["deploy"], str(ctx)],
            capture_output=True, text=True, timeout=10, input=""
        )
        cmd = r.stdout.strip().split("\n")[0]
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
    log.info("OpenClaw CTO v7.1 — enforce worker dirs")
    mode = "HOT-RESTART" if NO_BOOTSTRAP else "FULL BOOTSTRAP"
    log.info(f"Session: {SESSION} | Interval: {INTERVAL}s | Workers: {len(WORKERS)} | {mode}")
    log.info("=" * 50)

    if not NO_BOOTSTRAP:
        bootstrap()
    else:
        log.info("SKIP BOOTSTRAP — attaching to existing tmux workers")

    last_dispatch = [0.0] * len(WORKERS)
    last_cmd = [""] * len(WORKERS)
    last_answer = [0.0] * len(WORKERS)  # answer cooldown
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
            try:
                output = capture(pane)
                if not output.strip():
                    log.info(f"P{pane} ({worker['name']}): EMPTY OUTPUT")
                    continue
                ctx_match = re.findall(r'(\d+)%', output)
                ctx = int(ctx_match[-1]) if ctx_match else 0

                # Read actual dir from tmux
                actual_dir = get_actual_dir(output)
                expected_dir = worker["dir"]

                # ENFORCE: if worker drifted to wrong dir, send cd to correct dir
                if actual_dir != expected_dir and actual_dir != ".":
                    log.warning(f"P{pane} ({worker['name']}): DRIFT! expected={expected_dir} actual={actual_dir}")
                    if is_idle(output):
                        target = str(PROJECT_ROOT / expected_dir) if expected_dir != "." else str(PROJECT_ROOT)
                        # Use CC CLI !cd (shell escape) or plain prompt
                        try:
                            subprocess.run(["tmux", "send-keys", "-t", f"{SESSION}:0.{pane}", "-l",
                                          f"Change directory to {target} and work on project {worker['name']}"], timeout=8)
                            time.sleep(0.3)
                            subprocess.run(["tmux", "send-keys", "-t", f"{SESSION}:0.{pane}", "Enter"], timeout=5)
                        except:
                            pass
                        last_dispatch[i] = time.time()
                        log.info(f"P{pane} ({worker['name']}): CORRECTED -> cd {expected_dir}")
                    continue

                # Priority 0: Answer questions (with 60s cooldown)
                now = time.time()
                q_found, q_type = has_question(output)
                if q_found and (now - last_answer[i] > 60):
                    if q_type == "push":
                        if send_cmd(pane, "Yes, push to origin main"):
                            log.info(f"P{pane} ({worker['name']}): ANSWERED push")
                            last_answer[i] = now
                    else:
                        if send_cmd(pane, "Yes, proceed with all suggested actions."):
                            log.info(f"P{pane} ({worker['name']}): ANSWERED confirm")
                            last_answer[i] = now
                    continue

                if not is_idle(output):
                    log.info(f"P{pane} ({worker['name']} @ {actual_dir}): WORKING [ctx:{ctx}%]")
                    if any(x in output[-200:] for x in ["Enter to select", "Esc to cancel"]):
                        try:
                            subprocess.run(["tmux", "send-keys", "-t", f"{SESSION}:0.{pane}", "Enter"], timeout=5)
                        except:
                            pass
                    continue

                if dispatched >= 1:
                    log.info(f"P{pane} ({worker['name']}): IDLE (1-per-cycle)")
                    continue

                elapsed = now - last_dispatch[i]
                if elapsed < 90:
                    log.info(f"P{pane} ({worker['name']}): IDLE (cooldown {int(elapsed)}/90s)")
                    continue

                if ctx >= 85:
                    send_cmd(pane, "/compact")
                    last_dispatch[i] = now
                    dispatched += 1
                    continue

                # Use ASSIGNED worker info for brain (not drifted dir)
                log.info(f"P{pane} ({worker['name']} @ {actual_dir}): IDLE -> brain...")
                cmd = ask_brain(worker, ctx)

                if cmd:
                    cmd_key = cmd.split()[0]
                    if last_cmd[i] == cmd_key:
                        rotation = {
                            "/cook": f'/worker-build "Project: {worker["name"]}. Dir: {expected_dir}. Build+test." --fast',
                            "/worker-build": f'/eng-tech-debt "Project: {worker["name"]}. Dir: {expected_dir}. Scan." --fast',
                            "/eng-tech-debt": f'/dev-review "Project: {worker["name"]}. Dir: {expected_dir}. Review." --fast',
                            "/dev-review": f'/worker-test "Project: {worker["name"]}. Dir: {expected_dir}. Test." --fast',
                            "/worker-commit": f'/cto-review "Project: {worker["name"]}. Dir: {expected_dir}. Review." --fast',
                            "/worker-health": f'/cook "Project: {worker["name"]}. Dir: {expected_dir}. Continue." --fast',
                        }
                        cmd = rotation.get(cmd_key, f'/worker-health "Project: {worker["name"]}. Dir: {expected_dir}." --fast')
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
            except Exception as e:
                log.warning(f"P{pane}: ERROR {e}")
                continue

        rr_start = (rr_start + 1) % len(WORKERS)
        await asyncio.sleep(INTERVAL)

if __name__ == "__main__":
    asyncio.run(main())
