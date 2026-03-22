#!/usr/bin/env python3
"""OpenClaw CTO v7.5 — smart dispatch, no false positives, override dedup, heartbeat."""
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
LOG_FILE = Path(os.path.expanduser("~/.mekong/cto-daemon-stderr.log"))
NO_BOOTSTRAP = "--no-bootstrap" in sys.argv

WORKERS = [
    {"name": "mekong-cli", "dir": ".", "deploy": "pnpm run build"},
    {"name": "algo-trader", "dir": "apps/algo-trader", "deploy": "npx tsc --noEmit"},
    {"name": "well", "dir": "apps/well", "deploy": "npm run build"},
    {"name": "sophia-factory", "dir": "apps/sophia-factory", "deploy": "npm run build"},
    {"name": "apex-os", "dir": "apps/apex-os", "deploy": "npm run build"},
]

MISSION_DIR.mkdir(parents=True, exist_ok=True)
HEARTBEAT_FILE.parent.mkdir(parents=True, exist_ok=True)

# ===== SHELL ERROR PATTERNS (NOT real project errors) =====
SHELL_ERROR_NOISE = [
    "exit code", "timed out", "not a git repository", "failed to run git",
    "failed to determine", "command not found", "permission denied",
    "no such file", "enoent", "cannot find module", "module not found",
    "deprecat",  # deprecation warnings are not errors
]


def tmux_run(args):
    try:
        return subprocess.run(["tmux"] + args, capture_output=True, text=True, timeout=5).stdout
    except:
        return ""


def capture(pane):
    return tmux_run(["capture-pane", "-t", f"{SESSION}:0.{pane}", "-p", "-S", "-50"])


def get_actual_dir(output):
    match = re.findall(r"\U0001F4C1\s+(~?/[^\s]+)", output)
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
    tail_low = tail.lower()
    busy = ["running", "thinking", "tokens", "gusting", "crunching",
            "precipitating", "processing", "compacting", "considering",
            "smooshing", "mulling", "sautéed"]
    if any(x in tail_low for x in busy):
        return False
    return True


def has_question(output):
    if not is_idle(output):
        return False, "", ""
    lines8 = output.strip().split("\n")[-8:]
    tail_text = "\n".join(lines8)
    tail_low = tail_text.lower()
    if "?" not in tail_low or "unresolved" in tail_low:
        return False, "", ""
    if "push" in tail_low and ("remote" in tail_low or "origin" in tail_low):
        return True, "push", tail_text
    choice_markers = ["which", "choose", "select", "prefer", "option",
                      "would you like", "like me to", "tackle", "pick one",
                      "choose one", "what should"]
    if any(m in tail_low for m in choice_markers):
        return True, "choice", tail_text
    confirm_markers = ["do you want", "shall i", "should i", "proceed", "confirm",
                       "approve", "continue", "y/n", "yes/no", "go ahead",
                       "implement"]
    if any(m in tail_low for m in confirm_markers):
        return True, "confirm", tail_text
    return False, "", ""


def smart_answer(q_type, q_text, worker):
    low = q_text.lower()
    if q_type == "push":
        return "Yes, push to origin main"
    if q_type == "choice":
        if "fix" in low and "dep" in low:
            return "Fix the dependencies first — install missing packages."
        if "fix" in low and ("import" in low or "circular" in low):
            return "Fix the circular imports first."
        if "fix" in low and ("bug" in low or "error" in low):
            return "Fix the bugs first — that's highest priority."
        if "test" in low:
            return "Run the tests first to understand current state."
        return "Start with option 1 — the most impactful action first."
    # Default: approve recommendations
    if "implement" in low or "recommendation" in low:
        return "Yes, implement all recommendations."
    return "Yes, proceed with all suggested actions."


def read_worker_context(output):
    """v7.5: Read FRESH output between last two prompts. Much stricter error/test detection."""
    lines = output.strip().split("\n")
    # Find last prompt
    last_prompt_idx = -1
    for idx in range(len(lines) - 1, -1, -1):
        if "\u276f" in lines[idx]:
            last_prompt_idx = idx
            break
    if last_prompt_idx > 0:
        prev_prompt_idx = -1
        for idx in range(last_prompt_idx - 1, -1, -1):
            if "\u276f" in lines[idx]:
                prev_prompt_idx = idx
                break
        if prev_prompt_idx >= 0:
            fresh = lines[prev_prompt_idx:last_prompt_idx]
        else:
            fresh = lines[:last_prompt_idx]
    else:
        fresh = lines[-15:]

    text = "\n".join(fresh).lower()
    context = []

    # v7.5 FIX: Count REAL error lines, ignoring shell noise and "0 errors"
    error_lines = []
    for line in fresh:
        ll = line.lower()
        if ("error" in ll or "blocked" in ll):
            # Skip known noise patterns
            if re.search(r"(0 error|no error|without error|error.{0,5}free)", ll):
                continue
            if any(noise in ll for noise in SHELL_ERROR_NOISE):
                continue
            # Skip lines that are just status/summary (e.g. "✅ 0 errors")
            if re.search(r"[✅✓]\s*\d+\s*error", ll):
                continue
            error_lines.append(line)
    if len(error_lines) >= 2:  # Need at least 2 real error lines to trigger
        context.append("has_errors")

    # v7.5: Strict conflict detection (unchanged from v7.4)
    if "<<<<<<" in text or ">>>>>>>" in text or "merge conflict" in text:
        context.append("has_conflicts")

    if "commit" in text and ("success" in text or "created" in text):
        context.append("just_committed")
    if "review" in text and ("complete" in text or "done" in text):
        context.append("just_reviewed")

    # v7.5 FIX: Stricter test detection — look for actual test runner output
    test_pass_patterns = [r"\d+\s*pass", r"tests?\s*pass", r"all\s*tests?\s*(pass|green|ok)"]
    test_fail_patterns = [r"\d+\s*fail", r"tests?\s*fail", r"assert.*error"]
    if any(re.search(p, text) for p in test_pass_patterns):
        context.append("tests_passing")
    if any(re.search(p, text) for p in test_fail_patterns):
        if not re.search(r"(0 fail|no fail)", text):
            context.append("tests_failing")

    if "build" in text and ("success" in text or "green" in text):
        context.append("build_passing")
    if "compact" in text:
        context.append("compacting")
    return context


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
            capture_output=True, text=True, timeout=10, input="",
        )
        cmd = r.stdout.strip().split("\n")[0]
        parts = cmd.split(" /")
        if len(parts) > 1:
            cmd = parts[0]
        return cmd if cmd.startswith("/") else ""
    except:
        return ""


def context_override(worker, ctx, worker_ctx):
    """v7.5: Override only for REAL issues. Returns (cmd, category)."""
    d = worker["dir"]
    name = worker["name"]
    if "has_conflicts" in worker_ctx:
        return f'/fix "Project: {name}. Resolve all merge conflicts in {d}." --fast', "conflicts"
    if "has_errors" in worker_ctx and "tests_failing" not in worker_ctx:
        return f'/fix "Project: {name}. Fix all errors in {d}." --fast', "errors"
    if "tests_failing" in worker_ctx:
        return f'/fix "Project: {name}. Fix failing tests in {d}." --fast', "tests"
    if "just_committed" in worker_ctx and "tests_passing" in worker_ctx:
        return f'/cook "Project: {name}. Continue development in {d}." --fast', "post_commit"
    if "just_reviewed" in worker_ctx:
        return f'/cook "Project: {name}. Continue development in {d}." --fast', "post_review"
    return "", ""


# ===== MISSION QUEUE =====

def load_pending_missions():
    missions = []
    for f in sorted(MISSION_DIR.glob("*.json")):
        try:
            data = json.loads(f.read_text())
            if data.get("status") == "pending":
                missions.append({"file": f, **data})
        except:
            continue
    return missions


def claim_mission(mission, worker_name):
    try:
        data = json.loads(mission["file"].read_text())
        data["status"] = "in_progress"
        data["assigned_to"] = worker_name
        data["started_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        mission["file"].write_text(json.dumps(data, indent=2))
        return True
    except:
        return False


# ===== HEARTBEAT + LOG ROTATION =====

def write_heartbeat(cycle, workers_status):
    """Write heartbeat every cycle for Chairman monitoring."""
    try:
        now = time.strftime("%Y-%m-%d %H:%M:%S")
        lines = [
            f"# OpenClaw CTO Heartbeat",
            f"**Updated:** {now}",
            f"**Cycle:** {cycle}",
            f"**PID:** {os.getpid()}",
            f"**Version:** v7.5",
            "",
        ]
        for ws in workers_status:
            lines.append(f"- **P{ws['pane']} ({ws['name']})**: {ws['status']} [{ws['ctx']}%]")
        HEARTBEAT_FILE.write_text("\n".join(lines) + "\n")
    except:
        pass


def rotate_log_if_needed():
    """Rotate log when > 5MB."""
    try:
        if LOG_FILE.exists() and LOG_FILE.stat().st_size > 5 * 1024 * 1024:
            backup = LOG_FILE.with_suffix(".log.1")
            if backup.exists():
                backup.unlink()
            shutil.move(str(LOG_FILE), str(backup))
            log.info("LOG ROTATED (>5MB)")
    except:
        pass


# ===== BOOTSTRAP =====

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


# ===== MAIN LOOP =====

async def main():
    log.info("=" * 50)
    log.info("OpenClaw CTO v7.5.1 — 5 workers, brain v3, goal-oriented")
    mode = "HOT-RESTART" if NO_BOOTSTRAP else "FULL BOOTSTRAP"
    log.info(f"Session: {SESSION} | Interval: {INTERVAL}s | Workers: {len(WORKERS)} | {mode}")
    log.info("=" * 50)

    if not NO_BOOTSTRAP:
        bootstrap()
    else:
        log.info("SKIP BOOTSTRAP — attaching to existing tmux workers")

    last_dispatch = [0.0] * len(WORKERS)
    last_cmd = [""] * len(WORKERS)
    last_answer = [0.0] * len(WORKERS)
    compact_attempts = [0] * len(WORKERS)
    # v7.5: Track override attempts per worker per category
    override_attempts = [{} for _ in WORKERS]  # {category: count}
    MAX_OVERRIDE = 2  # Max times to send same override before giving up
    cycle = 0
    rr_start = 0

    while True:
        cycle += 1
        log.info(f"--- CYCLE {cycle} ---")

        if STOP_FILE.exists():
            log.info("KILLSWITCH ACTIVE")
            await asyncio.sleep(INTERVAL)
            continue

        # v7.5: Log rotation check every 50 cycles
        if cycle % 50 == 0:
            rotate_log_if_needed()

        dispatched = 0
        indices = [(rr_start + j) % len(WORKERS) for j in range(len(WORKERS))]
        workers_status = []

        # Load missions once per cycle
        pending_missions = load_pending_missions()
        if pending_missions:
            log.info(f"MISSIONS: {len(pending_missions)} pending")

        for i in indices:
            worker = WORKERS[i]
            pane = i
            try:
                output = capture(pane)
                if not output.strip():
                    workers_status.append({"pane": i, "name": worker["name"], "status": "EMPTY", "ctx": 0})
                    continue

                ctx_match = re.findall(r"(\d+)%", output)
                ctx = int(ctx_match[-1]) if ctx_match else 0
                actual_dir = get_actual_dir(output)
                expected_dir = worker["dir"]

                # Drift correction
                if actual_dir != expected_dir and actual_dir != ".":
                    log.warning(f"P{pane} ({worker['name']}): DRIFT! expected={expected_dir} actual={actual_dir}")
                    workers_status.append({"pane": i, "name": worker["name"], "status": "DRIFT", "ctx": ctx})
                    if is_idle(output):
                        target = str(PROJECT_ROOT / expected_dir) if expected_dir != "." else str(PROJECT_ROOT)
                        try:
                            subprocess.run(["tmux", "send-keys", "-t", f"{SESSION}:0.{pane}", "-l",
                                          f"Change directory to {target} and work on project {worker['name']}"], timeout=8)
                            time.sleep(0.3)
                            subprocess.run(["tmux", "send-keys", "-t", f"{SESSION}:0.{pane}", "Enter"], timeout=5)
                        except:
                            pass
                        last_dispatch[i] = time.time()
                    continue

                # Priority 0: Answer questions (60s cooldown)
                now = time.time()
                q_found, q_type, q_text = has_question(output)
                if q_found and (now - last_answer[i] > 60):
                    answer = smart_answer(q_type, q_text, worker)
                    if send_cmd(pane, answer):
                        log.info(f"P{pane} ({worker['name']}): ANSWERED [{q_type}] -> {answer[:60]}")
                        last_answer[i] = now
                    continue

                if not is_idle(output):
                    workers_status.append({"pane": i, "name": worker["name"], "status": "WORKING", "ctx": ctx})
                    log.info(f"P{pane} ({worker['name']} @ {actual_dir}): WORKING [ctx:{ctx}%]")
                    # Auto-dismiss menus
                    if any(x in output[-200:] for x in ["Enter to select", "Esc to cancel"]):
                        try:
                            subprocess.run(["tmux", "send-keys", "-t", f"{SESSION}:0.{pane}", "Enter"], timeout=5)
                        except:
                            pass
                    continue

                workers_status.append({"pane": i, "name": worker["name"], "status": "IDLE", "ctx": ctx})

                if dispatched >= 1:
                    log.info(f"P{pane} ({worker['name']}): IDLE (1-per-cycle)")
                    continue

                elapsed = now - last_dispatch[i]
                if elapsed < 90:
                    log.info(f"P{pane} ({worker['name']}): IDLE (cooldown {int(elapsed)}/90s)")
                    continue

                # Compact if context high
                if ctx >= 85:
                    if compact_attempts[i] >= 2:
                        log.warning(f"P{pane} ({worker['name']}): COMPACT FAILED {compact_attempts[i]}x — committing")
                        send_cmd(pane, f'/worker-commit "Project: {worker["name"]}. Save work before context reset." --fast')
                        compact_attempts[i] = 0
                    else:
                        send_cmd(pane, "/compact")
                        compact_attempts[i] += 1
                        log.info(f"P{pane} ({worker['name']}): COMPACT attempt {compact_attempts[i]} [ctx:{ctx}%]")
                    last_dispatch[i] = now
                    dispatched += 1
                    continue

                if ctx < 85:
                    compact_attempts[i] = 0

                # Read worker context (v7.5: much stricter)
                worker_ctx = read_worker_context(output)
                log.info(f"P{pane} ({worker['name']} @ {actual_dir}): IDLE ctx_signals={worker_ctx}")

                # v7.5: Context override with MAX attempt limit
                override, category = context_override(worker, ctx, worker_ctx)
                if override and category:
                    attempts = override_attempts[i].get(category, 0)
                    if attempts >= MAX_OVERRIDE:
                        log.info(f"P{pane}: OVERRIDE EXHAUSTED ({category} x{attempts}) -> skip to productive work")
                        override_attempts[i][category] = 0  # Reset for next time
                        # Fall through to mission/brain instead of looping
                    elif last_cmd[i] == override.split()[0]:
                        log.info(f"P{pane}: OVERRIDE DEDUP ({category}) -> skip to productive work")
                        override_attempts[i][category] = attempts + 1
                        # Fall through to mission/brain
                    else:
                        override_attempts[i][category] = attempts + 1
                        log.info(f"P{pane}: OVERRIDE [{category} #{attempts+1}] -> {override[:80]}")
                        if send_cmd(pane, override):
                            last_dispatch[i] = now
                            last_cmd[i] = override.split()[0]
                            dispatched += 1
                        continue
                else:
                    # No issues detected — reset override counters
                    override_attempts[i] = {}

                # v7.5: Mission queue (priority over brain)
                if pending_missions:
                    mission = pending_missions[0]
                    m_cmd = mission.get("command", "")
                    m_project = mission.get("project", "")
                    if m_cmd and (not m_project or m_project == worker["name"]):
                        if claim_mission(mission, worker["name"]):
                            log.info(f"P{pane}: MISSION -> {m_cmd[:80]}")
                            if send_cmd(pane, m_cmd):
                                last_dispatch[i] = now
                                last_cmd[i] = m_cmd.split()[0]
                                dispatched += 1
                                pending_missions.pop(0)
                            continue

                # Normal brain dispatch
                log.info(f"P{pane} ({worker['name']}): -> brain...")
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
                            "/pm-retro": f'/cook "Project: {worker["name"]}. Dir: {expected_dir}. Continue." --fast',
                            "/cto-review": f'/cook "Project: {worker["name"]}. Dir: {expected_dir}. Continue." --fast',
                        }
                        cmd = rotation.get(cmd_key, f'/cook "Project: {worker["name"]}. Dir: {expected_dir}. Continue." --fast')
                        cmd_key = cmd.split()[0]
                        log.info(f"P{pane}: DEDUP rotate -> {cmd_key}")

                    log.info(f"BRAIN -> P{pane} ({worker['name']}): {cmd[:80]}")
                    if send_cmd(pane, cmd):
                        last_dispatch[i] = now
                        last_cmd[i] = cmd_key
                        dispatched += 1
                else:
                    log.info(f"P{pane} ({worker['name']}): brain empty")
                    last_dispatch[i] = now
            except Exception as e:
                log.warning(f"P{pane}: ERROR {e}")
                continue

        # v7.5: Write heartbeat
        write_heartbeat(cycle, workers_status)

        rr_start = (rr_start + 1) % len(WORKERS)
        await asyncio.sleep(INTERVAL)


if __name__ == "__main__":
    asyncio.run(main())
