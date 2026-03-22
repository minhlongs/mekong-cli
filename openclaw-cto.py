#!/usr/bin/env python3
"""
OpenClaw CTO v8 — Full redesign. Simple. Robust. No bullshit.

Architecture:
  1. Monitor workers every 20s
  2. If idle + cooldown expired → ask Brain for mission → send it
  3. If question → answer it
  4. If context >= 80% → compact
  5. That's it. No override, no dedup, no rotation, no animation parsing.
"""
import asyncio, json, logging, os, subprocess, sys, time, re, shutil
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [CTO] %(message)s")
log = logging.getLogger("cto")

SESSION = os.environ.get("CTO_SESSION", "openclaw")
INTERVAL = int(os.environ.get("CTO_INTERVAL", "20"))
PROJECT_ROOT = Path(os.path.expanduser("~/mekong-cli"))
STOP_FILE = Path(os.path.expanduser("~/.openclaw/STOP"))
HEARTBEAT_FILE = Path(os.path.expanduser("~/.openclaw/HEARTBEAT.md"))
MISSION_DIR = Path(os.path.expanduser("~/.mekong/missions"))
NO_BOOTSTRAP = "--no-bootstrap" in sys.argv
COOLDOWN = 300  # 5 minutes between dispatches — let workers WORK

WORKERS = [
    {"name": "mekong-cli", "dir": ".", "deploy": "pnpm run build"},
    {"name": "algo-trader", "dir": "apps/algo-trader", "deploy": "npx tsc --noEmit"},
    {"name": "well", "dir": "apps/well", "deploy": "npm run build"},
    {"name": "sophia-factory", "dir": "apps/sophia-factory", "deploy": "npm run build"},
    {"name": "apex-os", "dir": "apps/apex-os", "deploy": "npm run build"},
]

MISSION_DIR.mkdir(parents=True, exist_ok=True)
HEARTBEAT_FILE.parent.mkdir(parents=True, exist_ok=True)


def tmux(args):
    try:
        return subprocess.run(["tmux"] + args, capture_output=True, text=True, timeout=5).stdout
    except:
        return ""


def capture(pane):
    return tmux(["capture-pane", "-t", f"{SESSION}:0.{pane}", "-p", "-S", "-30"])


def get_ctx(output):
    """Extract context window percentage. v8.1: Only match 'Context: N%' pattern."""
    # More specific regex to avoid catching "Build 85%" or "Tests 100%"
    m = re.search(r"Context[:\s]+(\d+)%|(\d+)%\s*used", output, re.IGNORECASE)
    if m:
        return int(m.group(1) or m.group(2))
    return 0


def is_idle(output):
    """v8.1: Check if ❯ prompt visible in last 8 lines AND no active work happening."""
    tail = "\n".join(output.strip().split("\n")[-8:])
    if "\u276f" not in tail:
        return False
    low = tail.lower()
    # Active work indicators — if any present, not idle
    # v8.1: Added 10+ patterns from v7.5 to avoid false idle detection
    active = ["compacting", "thinking", "running", "precipitating",
              "considering", "pondering", "loading", "fetching",
              "processing", "dilly-dallying", "flummoxing",
              "press up to edit", "enter to select", "queued message",
              "harmonizing", "smooshing", "worked for", "working",
              "mulling", "crunching", "gusting", "sautéed"]
    return not any(a in low for a in active)


def has_pending_tasks(output):
    """Worker has its own task queue — don't interrupt."""
    low = output[-500:].lower()
    m = re.search(r"(\d+)\s*pending", low)
    return int(m.group(1)) > 0 if m else False


def detect_question(output):
    """Detect if worker is asking something."""
    if not is_idle(output):
        # Check for interactive menus even when not "idle"
        tail = output[-300:]
        if "Enter to select" in tail and "navigate" in tail:
            return "menu"
        if "Press up to edit" in tail:
            return "queued"
        return ""
    lines = output.strip().split("\n")[-10:]
    text = "\n".join(lines)
    low = text.lower()
    # Numbered options
    if len(re.findall(r"^\s*\d+\.\s+\w", text, re.MULTILINE)) >= 2:
        return "choice"
    if "?" not in low:
        return ""
    if "push" in low and ("remote" in low or "origin" in low):
        return "push"
    if any(m in low for m in ["which", "choose", "select", "option", "would you like"]):
        return "choice"
    if any(m in low for m in ["do you want", "shall i", "should i", "proceed", "y/n"]):
        return "confirm"
    return ""


def answer(q_type):
    if q_type == "push":
        return "Yes, push to origin main"
    if q_type == "menu":
        return None  # Will send Enter
    if q_type == "queued":
        return None  # Will send Escape
    if q_type == "choice":
        return "Start with option 1 — the most impactful action first."
    return "Yes, proceed."


def send(pane, text, worker=None):
    """Send text to pane. Returns True if command was sent, False if failed or dismissed."""
    try:
        # Check for queued messages — dismiss first
        out = capture(pane)
        if "Press up to edit" in out[-300:]:
            subprocess.run(["tmux", "send-keys", "-t", f"{SESSION}:0.{pane}", "Escape"], timeout=5)
            time.sleep(0.5)
            return True  # Successfully dismissed, not an error
        # v8.2: NO cd command — Brain includes dir in mission. CC CLI handles navigation.
        # Send the actual command
        subprocess.run(["tmux", "send-keys", "-t", f"{SESSION}:0.{pane}", "-l", text], timeout=8)
        time.sleep(0.3)
        subprocess.run(["tmux", "send-keys", "-t", f"{SESSION}:0.{pane}", "Enter"], timeout=5)
        log.info(f"P{pane}: SENT {text[:80]}")
        return True
    except Exception as e:
        log.warning(f"P{pane}: SEND FAILED: {e}")
        return False


def ask_brain(worker, ctx):
    """Ask Brain for mission. Timeout 20s (not 45s) to avoid blocking."""
    try:
        r = subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "scripts" / "cto-brain.py"),
             worker["name"], worker["dir"], worker["deploy"], str(ctx)],
            capture_output=True, text=True, timeout=20, input="",
        )
        if r.returncode != 0:
            log.warning(f"BRAIN({worker['name']}) failed: {r.stderr[:100] if r.stderr else 'unknown'}")
        return r.stdout.strip().split("\n")[0] if r.stdout.strip() else ""
    except subprocess.TimeoutExpired:
        log.warning(f"BRAIN({worker['name']}) timeout >20s")
        return ""
    except Exception as e:
        log.warning(f"BRAIN({worker['name']}) error: {e}")
        return ""


def load_missions():
    missions = []
    for f in sorted(MISSION_DIR.glob("*.json")):
        try:
            d = json.loads(f.read_text())
            if d.get("status") == "pending":
                missions.append({"file": f, **d})
        except:
            continue
    return missions


def claim_mission(m, worker):
    try:
        d = json.loads(m["file"].read_text())
        d["status"] = "in_progress"
        d["assigned_to"] = worker
        d["started_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        m["file"].write_text(json.dumps(d, indent=2))
        return True
    except:
        return False


def bootstrap():
    subprocess.run(["tmux", "kill-session", "-t", SESSION], capture_output=True)
    time.sleep(1)
    subprocess.run(["tmux", "new-session", "-d", "-s", SESSION, "-x", "200", "-y", "60"])
    for i in range(1, len(WORKERS)):
        subprocess.run(["tmux", "split-window", "-t", f"{SESSION}:0"])
    subprocess.run(["tmux", "select-layout", "-t", SESSION, "tiled"])
    time.sleep(1)
    for i, w in enumerate(WORKERS):
        subprocess.run(["tmux", "send-keys", "-t", f"{SESSION}:0.{i}",
                        f"source ~/.zshrc 2>/dev/null && cd {PROJECT_ROOT} && mekong --interactive", "Enter"])
    time.sleep(15)
    for i in range(len(WORKERS)):
        if "trust this folder" in capture(i):
            subprocess.run(["tmux", "send-keys", "-t", f"{SESSION}:0.{i}", "Enter"])
    time.sleep(3)
    log.info("BOOTSTRAP: done")


async def main():
    log.info("=" * 40)
    log.info("OpenClaw CTO v8 — clean redesign")
    log.info(f"Workers: {len(WORKERS)} | Interval: {INTERVAL}s | Cooldown: {COOLDOWN}s")
    log.info("=" * 40)

    if not NO_BOOTSTRAP:
        bootstrap()
    else:
        log.info("HOT-RESTART — attaching to existing workers")

    last_dispatch = [0.0] * len(WORKERS)
    cycle = 0

    while True:
        cycle += 1
        if STOP_FILE.exists():
            log.info(f"C{cycle}: KILLSWITCH")
            await asyncio.sleep(INTERVAL)
            continue

        missions = load_missions()
        now = time.time()
        statuses = []

        for i, worker in enumerate(WORKERS):
            output = capture(i)
            if not output.strip():
                statuses.append(f"P{i}({worker['name']}):EMPTY")
                continue

            ctx = get_ctx(output)

            # 1. Handle questions/menus
            q = detect_question(output)
            if q:
                if q == "menu":
                    subprocess.run(["tmux", "send-keys", "-t", f"{SESSION}:0.{i}", "Enter"], timeout=5)
                    log.info(f"P{i}({worker['name']}): MENU → Enter")
                elif q == "queued":
                    subprocess.run(["tmux", "send-keys", "-t", f"{SESSION}:0.{i}", "Escape"], timeout=5)
                    log.info(f"P{i}({worker['name']}): QUEUED → Escape")
                else:
                    a = answer(q)
                    send(i, a)
                    log.info(f"P{i}({worker['name']}): Q[{q}] → {a[:40]}")
                continue

            # 2. Not idle → working (but check for stuck shells)
            if not is_idle(output):
                # Detect stuck shell — "shell still running" means something hung
                if "shell still running" in output[-300:].lower():
                    if not hasattr(main, '_shell_stuck'):
                        main._shell_stuck = [0] * len(WORKERS)
                    main._shell_stuck[i] += 1
                    if main._shell_stuck[i] >= 5:  # 5 cycles = 100s stuck
                        try:
                            subprocess.run(["tmux", "send-keys", "-t", f"{SESSION}:0.{i}", "C-c"], timeout=5)
                            log.info(f"P{i}({worker['name']}): STUCK SHELL → Ctrl-C")
                            main._shell_stuck[i] = 0
                        except:
                            pass
                else:
                    if hasattr(main, '_shell_stuck'):
                        main._shell_stuck[i] = 0
                statuses.append(f"P{i}({worker['name']}):WORK[{ctx}%]")
                continue

            # 3. Has own pending tasks → let it self-direct
            if has_pending_tasks(output):
                statuses.append(f"P{i}({worker['name']}):SELF[{ctx}%]")
                continue

            # 3b. CRITICAL OVERRIDE: Detect merge conflicts, failing tests, build errors
            # If found, auto-fix before assigning new work (P0 fix)
            output_full = output.lower()

            # Merge conflicts
            if "<<<<<<<" in output or ">>>>>>> " in output or "conflict" in output_full:
                cmd = f"/fix merge conflicts in {worker['dir']} — check git status, resolve conflicts, keep main branch changes, commit"
                send(i, cmd)
                log.info(f"P{i}({worker['name']}): MERGE CONFLICT → auto-fix")
                last_dispatch[i] = now
                statuses.append(f"P{i}({worker['name']}):CONFLICT[{ctx}%]")
                continue

            # Failing tests (but not during test run)
            if "test" in output_full and ("fail" in output_full or "error" in output_full):
                if "running" not in output_full and "pass" not in output_full[-200:]:
                    cmd = f"/fix failing tests in {worker['dir']} — read test output, fix the code or tests, ensure 100% pass"
                    send(i, cmd)
                    log.info(f"P{i}({worker['name']}): FAILING TEST → auto-fix")
                    last_dispatch[i] = now
                    statuses.append(f"P{i}({worker['name']}):FIX-TEST[{ctx}%]")
                    continue

            # Build errors (not just warnings)
            build_errors = ["build failed", "compilation failed", "syntaxerror", "typeerror", "module not found"]
            if any(e in output_full for e in build_errors):
                cmd = f"/fix build errors in {worker['dir']} — run build, read errors, fix code, verify build passes"
                send(i, cmd)
                log.info(f"P{i}({worker['name']}): BUILD ERROR → auto-fix")
                last_dispatch[i] = now
                statuses.append(f"P{i}({worker['name']}):FIX-BUILD[{ctx}%]")
                continue

            # 4. Context high → compact (or /clear if compact keeps failing)
            if ctx >= 80:
                out_tail = output[-300:]
                if "error compacting" in out_tail.lower():
                    send(i, "/clear")
                    log.info(f"P{i}({worker['name']}): COMPACT ERROR → /clear")
                else:
                    send(i, "/compact")
                last_dispatch[i] = now
                statuses.append(f"P{i}({worker['name']}):COMPACT[{ctx}%]")
                continue

            # 5. Cooldown
            elapsed = now - last_dispatch[i]
            if elapsed < COOLDOWN:
                statuses.append(f"P{i}({worker['name']}):COOL[{int(elapsed)}/{COOLDOWN}s]")
                continue

            # 6. DISPATCH: mission queue first, then brain
            cmd = ""
            if missions:
                m = missions[0]
                mc = m.get("command", "")
                mp = m.get("project", "")
                if mc and (not mp or mp == worker["name"]):
                    if claim_mission(m, worker["name"]):
                        cmd = mc
                        missions.pop(0)
                        log.info(f"P{i}({worker['name']}): MISSION → {cmd[:60]}")

            if not cmd:
                cmd = ask_brain(worker, ctx)
                if cmd:
                    log.info(f"P{i}({worker['name']}): BRAIN → {cmd[:60]}")

            if cmd:
                send(i, cmd, worker)
                last_dispatch[i] = now
                statuses.append(f"P{i}({worker['name']}):SENT[{ctx}%]")
            else:
                statuses.append(f"P{i}({worker['name']}):IDLE[{ctx}%]")
                last_dispatch[i] = now

        # Heartbeat
        try:
            HEARTBEAT_FILE.write_text(
                f"# CTO v8 Heartbeat\n"
                f"**Cycle:** {cycle} | **PID:** {os.getpid()} | **Time:** {time.strftime('%H:%M:%S')}\n\n"
                + "\n".join(f"- {s}" for s in statuses) + "\n"
            )
        except:
            pass

        log.info(f"C{cycle}: {' | '.join(statuses)}")
        await asyncio.sleep(INTERVAL)


if __name__ == "__main__":
    asyncio.run(main())
