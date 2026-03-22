#!/usr/bin/env python3
"""OpenClaw CTO v7.3 — fix P1 false-busy + compact loop."""
import asyncio, json, logging, os, subprocess, sys, time, re
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [CTO] %(message)s")
log = logging.getLogger("cto")

SESSION = os.environ.get("CTO_SESSION", "openclaw")
INTERVAL = int(os.environ.get("CTO_INTERVAL", "20"))
PROJECT_ROOT = Path(os.path.expanduser("~/mekong-cli"))
STOP_FILE = Path(os.path.expanduser("~/.openclaw/STOP"))
NO_BOOTSTRAP = "--no-bootstrap" in sys.argv

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
    return tmux_run(["capture-pane", "-t", f"{SESSION}:0.{pane}", "-p", "-S", "-50"])

def get_actual_dir(output):
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
    # Only check busy indicators in tail — prompt present = idle
    tail_low = tail.lower()
    busy = ["running", "thinking", "tokens", "gusting", "crunching",
            "precipitating", "processing", "compacting"]
    if any(x in tail_low for x in busy):
        return False
    return True

def has_question(output):
    """Detect real questions in last 8 lines — expanded markers."""
    if not is_idle(output):
        return False, "", ""
    lines8 = output.strip().split("\n")[-8:]
    tail_text = "\n".join(lines8)
    tail_low = tail_text.lower()
    if "?" not in tail_low:
        return False, "", ""
    if "unresolved" in tail_low:
        return False, "", ""
    # Push question
    if "push" in tail_low and ("remote" in tail_low or "origin" in tail_low):
        return True, "push", tail_text
    # Choice question — worker asking which option
    choice_markers = ["which", "choose", "select", "prefer", "option",
                      "would you like", "like me to", "tackle", "pick one",
                      "choose one", "what should"]
    if any(m in tail_low for m in choice_markers):
        return True, "choice", tail_text
    # Yes/no confirmation
    confirm_markers = ["do you want", "shall i", "should i", "proceed", "confirm",
                       "approve", "continue", "y/n", "yes/no", "go ahead"]
    if any(m in tail_low for m in confirm_markers):
        return True, "confirm", tail_text
    return False, "", ""

def smart_answer(q_type, q_text, worker):
    """Generate context-aware answer based on question type and content."""
    low = q_text.lower()
    if q_type == "push":
        return "Yes, push to origin main"
    if q_type == "choice":
        # Priority: fix bugs > fix deps > fix imports > test > build > review
        if "fix" in low and "dep" in low:
            return "Fix the dependencies first — install missing packages."
        if "fix" in low and ("import" in low or "circular" in low):
            return "Fix the circular imports first."
        if "fix" in low and ("bug" in low or "error" in low):
            return "Fix the bugs first — that's highest priority."
        if "test" in low:
            return "Run the tests first to understand current state."
        if "push" in low:
            return "Push to remote after fixing all issues."
        # Default for choice: pick first actionable option
        return "Start with option 1 — the most impactful action first."
    # Default confirm
    return "Yes, proceed with all suggested actions."

def read_worker_context(output):
    """Read lines AFTER last prompt to understand current state only."""
    lines = output.strip().split("\n")
    # Find last prompt line to only read FRESH output
    last_prompt_idx = -1
    for idx in range(len(lines) - 1, -1, -1):
        if "\u276f" in lines[idx]:
            last_prompt_idx = idx
            break
    # Read lines between second-to-last prompt and last prompt (= last command output)
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
    if ("error" in text or "blocked" in text) and "0 error" not in text:
        context.append("has_errors")
    if "conflict" in text or "<<<<<<" in text:
        context.append("has_conflicts")
    if "commit" in text and ("success" in text or "created" in text):
        context.append("just_committed")
    if "review" in text and ("complete" in text or "done" in text):
        context.append("just_reviewed")
    if "test" in text and ("pass" in text or "green" in text):
        context.append("tests_passing")
    if "test" in text and ("fail" in text or "red" in text) and "0 fail" not in text:
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
            capture_output=True, text=True, timeout=10, input=""
        )
        cmd = r.stdout.strip().split("\n")[0]
        parts = cmd.split(" /")
        if len(parts) > 1:
            cmd = parts[0]
        return cmd if cmd.startswith("/") else ""
    except:
        return ""

def context_override(worker, ctx, worker_ctx):
    """Override brain decision based on what worker actually needs."""
    d = worker["dir"]
    name = worker["name"]
    # Worker has merge conflicts — fix first
    if "has_conflicts" in worker_ctx:
        return f'/fix "Project: {name}. Resolve all merge conflicts in {d}." --fast'
    # Worker has errors — fix first
    if "has_errors" in worker_ctx and "tests_failing" not in worker_ctx:
        return f'/fix "Project: {name}. Fix all errors in {d}." --fast'
    # Tests failing — fix tests
    if "tests_failing" in worker_ctx:
        return f'/fix "Project: {name}. Fix failing tests in {d}." --fast'
    # Just committed + tests passing → deploy/review
    if "just_committed" in worker_ctx and "tests_passing" in worker_ctx:
        return f'/cto-review "Project: {name}. Post-commit review." --fast'
    # Just reviewed → next phase (build/test/ship)
    if "just_reviewed" in worker_ctx:
        return f'/cook "Project: {name}. Continue development in {d}." --fast'
    return ""  # No override, let brain decide

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
    log.info("OpenClaw CTO v7.3 — fix false-busy + compact loop")
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
    compact_attempts = [0] * len(WORKERS)  # track compact failures
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
                actual_dir = get_actual_dir(output)
                expected_dir = worker["dir"]

                # ENFORCE: drift correction via natural language
                if actual_dir != expected_dir and actual_dir != ".":
                    log.warning(f"P{pane} ({worker['name']}): DRIFT! expected={expected_dir} actual={actual_dir}")
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
                        log.info(f"P{pane} ({worker['name']}): CORRECTED -> cd {expected_dir}")
                    continue

                # Priority 0: Answer questions (60s cooldown) — SMART answers
                now = time.time()
                q_found, q_type, q_text = has_question(output)
                if q_found and (now - last_answer[i] > 60):
                    answer = smart_answer(q_type, q_text, worker)
                    if send_cmd(pane, answer):
                        log.info(f"P{pane} ({worker['name']}): ANSWERED [{q_type}] -> {answer[:60]}")
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
                    if compact_attempts[i] >= 2:
                        # Compact failed 2x — commit work and let worker continue
                        log.warning(f"P{pane} ({worker['name']}): COMPACT FAILED {compact_attempts[i]}x at {ctx}% — committing instead")
                        send_cmd(pane, f'/worker-commit "Project: {worker["name"]}. Save work before context reset." --fast')
                        compact_attempts[i] = 0
                    else:
                        send_cmd(pane, "/compact")
                        compact_attempts[i] += 1
                        log.info(f"P{pane} ({worker['name']}): COMPACT attempt {compact_attempts[i]} [ctx:{ctx}%]")
                    last_dispatch[i] = now
                    dispatched += 1
                    continue

                # Reset compact counter when ctx healthy
                if ctx < 85:
                    compact_attempts[i] = 0

                # READ WORKER CONTEXT before dispatching
                worker_ctx = read_worker_context(output)
                log.info(f"P{pane} ({worker['name']} @ {actual_dir}): IDLE ctx_signals={worker_ctx}")

                # Context override: if worker has specific needs, skip brain
                # But DEDUP: don't repeat same override — fall through to brain
                override = context_override(worker, ctx, worker_ctx)
                override_key = override.split()[0] if override else ""
                if override and last_cmd[i] != override_key:
                    log.info(f"P{pane}: CONTEXT OVERRIDE -> {override[:80]}")
                    if send_cmd(pane, override):
                        last_dispatch[i] = now
                        last_cmd[i] = override_key
                        dispatched += 1
                        log.info(f"DELEGATED P{pane} ({worker['name']}) -> {override_key} [OVERRIDE]")
                    continue
                elif override:
                    log.info(f"P{pane}: OVERRIDE DEDUP (already sent {override_key}) -> brain fallback")

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
