"""OpenClaw Autonomous Daemon — Paperclip Model.

Runs CONTINUOUSLY on M1 Max. Every cycle:
1. Pick next priority mission
2. Execute via direct Ollama (qwen3:32b)
3. Auto-publish content to GitHub Discussions
4. Sleep 12 hours, repeat

This IS the a16z solo company: agents do everything, human sleeps.
"""
import json
import os
import sys
import time
import datetime
import hashlib
import fcntl
import requests
from pathlib import Path

# Config
GATEWAY_URL = os.getenv("GATEWAY_URL", "http://localhost:8000")
REPORTS_DIR = Path.home() / "mekong-cli" / "content" / "openclaw-reports"
STATE_FILE = Path.home() / ".mekong" / "daemon-state.json"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GITHUB_REPO = "longtho638-jpg/mekong-cli"
CYCLE_INTERVAL_HOURS = 12
PID_FILE = Path.home() / ".mekong" / "daemon.pid"

# Mission queue — rotates each cycle, never repeats within 24h
MISSIONS = [
    # Wave 1: Content that attracts organic traffic
    {"dept": "content", "goal": "Write a blog post: '5 Ways Solo Founders Use Automation to Replace a 10-Person Team'. Include practical examples with mekong CLI commands. Target SEO keywords: solo founder automation, one-person company tools.", "publish": True, "category": "Show and tell"},
    {"dept": "content", "goal": "Write a blog post: 'How to Run Your Entire Business From the Terminal'. Show real mekong commands for sales, finance, HR, marketing. Target SEO: terminal business tools, CLI automation.", "publish": True, "category": "Show and tell"},
    {"dept": "content", "goal": "Write a tutorial: 'Getting Started with Mekong IDE — Your First 5 Commands'. Step-by-step from install to first mission. Include curl examples for managed API.", "publish": True, "category": "General"},

    # Wave 2: Market intelligence (feeds back into strategy)
    {"dept": "analyst", "goal": "Competitive analysis: Mekong IDE vs Cursor vs Windsurf vs Claude Code vs OpenCode. Compare: pricing, features, local LLM support, command count, self-hosting. Output as markdown table.", "publish": True, "category": "General"},
    {"dept": "marketing", "goal": "Find 20 online communities where solo founders and solopreneurs hang out. List: name, URL, size, posting rules, best content format. Focus on communities that welcome tool recommendations.", "publish": False},

    # Wave 3: Sales pipeline (identify potential customers)
    {"dept": "sales", "goal": "Build an ideal customer profile for Mekong IDE. Who would pay $49/mo for 290 business automation commands? List 5 personas with: role, pain point, how they'd use Mekong, where to reach them.", "publish": False},
    {"dept": "growth", "goal": "Design 3 growth experiments for Mekong IDE user acquisition. Each experiment: hypothesis, channel, content, metric, timeline. Focus on zero-budget tactics.", "publish": False},

    # Wave 4: Operations (keep the machine running)
    {"dept": "ops", "goal": "Generate operations status report: check if api.cashclaw.cc is healthy, mekongmind.pages.dev is live, Ollama is running, gateway response time. Report any issues.", "publish": False},
    {"dept": "security", "goal": "Security audit of the gateway API at localhost:8000. Check: CORS headers, auth flow, rate limiting, input validation. List any vulnerabilities found.", "publish": False},
    {"dept": "legal", "goal": "Draft a minimal Terms of Service for mekongmind.com. Cover: service description, pricing, refunds, liability, data handling. Keep under 1000 words. Do NOT use the word AI — use 'automation' instead.", "publish": True, "category": "General"},
]

REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# ── SELL: Every piece of content ends with this CTA ──
SELL_CTA = """

---

**Run your entire company with 22 autonomous departments. $49/mo.**

- [Start free (50 credits)](https://mekongmind.pages.dev)
- [Subscribe $49/mo](https://buy.polar.sh/a09a5fa0-63db-42a4-a547-3b1523ffc263)
- [Self-host free (MIT)](https://github.com/longtho638-jpg/mekong-cli)

*Generated autonomously by MekongMind — the one-person company platform.*
"""


def load_state() -> dict:
    """Load daemon state (completed missions, last cycle time)."""
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"completed": {}, "cycle_count": 0, "total_missions": 0}


def save_state(state: dict):
    """Persist daemon state."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))


def mission_hash(mission: dict) -> str:
    """Unique hash for a mission (to avoid repeats within 24h)."""
    return hashlib.md5(mission["goal"][:100].encode()).hexdigest()[:12]


def get_api_key() -> str:
    """Get or create a daemon API key via gateway onboard."""
    key_file = Path.home() / ".mekong" / "daemon-api-key.txt"
    if key_file.exists():
        return key_file.read_text().strip()

    try:
        r = requests.post(f"{GATEWAY_URL}/v1/onboard", json={
            "name": "OpenClaw Daemon",
            "email": "daemon@openclaw.local",
        }, timeout=10)
        if r.status_code == 200:
            key = r.json()["api_key"]
            key_file.write_text(key)
            return key
    except Exception as e:
        print(f"  [ERROR] Onboard failed: {e}")
    return ""


def execute_mission(goal: str, api_key: str) -> str:
    """Execute mission via Ollama native API (non-streaming, no credit cost).

    Uses Ollama's native /api/chat endpoint which handles model loading
    and memory management better than OpenAI-compatible endpoint.
    """
    model = os.getenv("DAEMON_LLM_MODEL", "qwen3:32b")
    system_prompt = (
        "You are an expert business consultant writing for solo founders. "
        "Write detailed, actionable, well-structured content with headers and bullet points. "
        "Do NOT use the word 'AI' — use 'automation' or 'intelligent' instead. "
        "Minimum 500 words. Include specific examples."
    )
    try:
        r = requests.post("http://localhost:11434/api/chat",
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": goal},
                ],
                "stream": False,
                "options": {"num_predict": 2000, "temperature": 0.7},
            }, timeout=300)  # 5 min for thorough content
        content = r.json()["message"]["content"]
        if len(content) > 100:
            return content
        return f"[SHORT] {len(content)} chars — model may be overloaded"
    except requests.Timeout:
        return "[TIMEOUT] Ollama took >5 minutes"
    except Exception as e:
        return f"[ERROR] {e}"


def publish_to_github(title: str, body: str, category: str = "General") -> str:
    """Auto-publish content as GitHub Discussion. Returns URL or empty string."""
    if not GITHUB_TOKEN:
        print("  [SKIP] No GITHUB_TOKEN — cannot publish")
        return ""

    # Get category ID
    categories = {
        "Announcements": "DIC_kwDOQo7oj84C5Ew4",
        "General": "DIC_kwDOQo7oj84C5Ew5",
        "Ideas": "DIC_kwDOQo7oj84C5Ew7",
        "Show and tell": "DIC_kwDOQo7oj84C5Ew8",
    }
    cat_id = categories.get(category, categories["General"])

    # Get repo ID
    try:
        headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}
        query = """query { repository(owner:"%s", name:"%s") { id } }""" % tuple(GITHUB_REPO.split("/"))
        r = requests.post("https://api.github.com/graphql",
            json={"query": query},
            headers=headers, timeout=10)
        repo_id = r.json()["data"]["repository"]["id"]

        # Create discussion
        mutation = """mutation {
            createDiscussion(input: {
                repositoryId: "%s",
                categoryId: "%s",
                title: "%s",
                body: "%s"
            }) { discussion { url } }
        }""" % (repo_id, cat_id, title.replace('"', '\\"'), body.replace('"', '\\"').replace("\n", "\\n"))

        r = requests.post("https://api.github.com/graphql",
            json={"query": mutation},
            headers=headers, timeout=10)
        url = r.json().get("data", {}).get("createDiscussion", {}).get("discussion", {}).get("url", "")
        if url:
            print(f"  [PUBLISHED] {url}")
            return url
    except Exception as e:
        print(f"  [PUBLISH_ERROR] {e}")
    return ""


def run_cycle(state: dict) -> dict:
    """Run one complete daemon cycle."""
    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M")
    cycle = state["cycle_count"] + 1
    now = time.time()

    print(f"\n{'=' * 60}")
    print(f"  OpenClaw Daemon — Cycle #{cycle}")
    print(f"  Time: {ts}")
    print(f"  Missions: {len(MISSIONS)} queued")
    print(f"{'=' * 60}")

    api_key = get_api_key()
    if not api_key:
        print("  [FATAL] Cannot get API key — skipping cycle")
        return state

    completed_this_cycle = 0

    for i, mission in enumerate(MISSIONS):
        mhash = mission_hash(mission)

        # Skip if completed within 24h
        last_run = state["completed"].get(mhash, 0)
        if now - last_run < 86400:
            print(f"\n  [{i+1}/{len(MISSIONS)}] SKIP (ran {int((now-last_run)/3600)}h ago): {mission['goal'][:60]}...")
            continue

        print(f"\n  [{i+1}/{len(MISSIONS)}] {mission['dept']}: {mission['goal'][:60]}...")

        result = execute_mission(mission["goal"], api_key)

        # Save report locally
        filename = f"{ts}-{mission['dept']}-{mhash}.md"
        filepath = REPORTS_DIR / filename
        filepath.write_text(
            f"# {mission['goal']}\n\n"
            f"**Department:** {mission['dept']} | **Cycle:** {cycle}\n"
            f"**Generated:** {ts}\n\n---\n\n{result}"
        )
        print(f"  Report: {filename} ({len(result)} chars)")

        # ── SELL: inject CTA into every piece of content ──
        result_with_cta = (result + SELL_CTA) if (result and len(result) > 100 and not result.startswith("[")) else result

        # ── PUBLISH: auto-post content to GitHub ──
        published_url = ""
        if mission.get("publish") and result and len(result) > 100 and not result.startswith("["):
            title = mission["goal"][:100]
            published_url = publish_to_github(title, result_with_cta, mission.get("category", "General")) or ""

        # ── REPORT: track what happened ──
        run_record = {
            "hash": mhash,
            "dept": mission["dept"],
            "goal": mission["goal"][:80],
            "chars": len(result),
            "published": bool(published_url),
            "published_url": published_url or "",
            "ts": now,
        }
        if "runs" not in state:
            state["runs"] = []
        state["runs"].append(run_record)
        # Keep last 100 runs
        state["runs"] = state["runs"][-100:]

        state["completed"][mhash] = now
        state["total_missions"] = state.get("total_missions", 0) + 1
        completed_this_cycle += 1
        save_state(state)  # Save after EACH mission (crash-safe)
        time.sleep(5)  # Cool down

    state["cycle_count"] = cycle

    # ── ITERATE: analyze what worked, adjust priorities ──
    print(f"\n  --- Paperclip Iterate ---")
    runs = state.get("runs", [])
    if len(runs) >= 5:
        published = [r for r in runs if r.get("published")]
        failed = [r for r in runs if r.get("chars", 0) < 100]
        dept_scores = {}
        for r in runs[-20:]:  # Last 20 runs
            dept = r.get("dept", "unknown")
            score = dept_scores.get(dept, {"published": 0, "total": 0, "chars": 0})
            score["total"] += 1
            score["chars"] += r.get("chars", 0)
            if r.get("published"):
                score["published"] += 1
            dept_scores[dept] = score

        # Log iteration insights
        for dept, score in sorted(dept_scores.items(), key=lambda x: x[1]["chars"], reverse=True):
            rate = score["published"] / max(score["total"], 1) * 100
            print(f"  {dept:12s}: {score['total']} runs, {score['published']} published ({rate:.0f}%), avg {score['chars']//max(score['total'],1)} chars")

        # Store insights for next cycle
        state["iterate_insights"] = {
            "best_dept": max(dept_scores, key=lambda d: dept_scores[d]["chars"]) if dept_scores else "content",
            "publish_rate": len(published) / max(len(runs), 1) * 100,
            "total_published": len(published),
        }
        print(f"  Best dept: {state['iterate_insights']['best_dept']}, Publish rate: {state['iterate_insights']['publish_rate']:.0f}%")
    else:
        print(f"  Not enough data yet ({len(runs)} runs, need 5+)")

    save_state(state)

    # ── TENANT AUTOPILOT ── Run all customer daemons
    print(f"\n  --- Running tenant autopilots ---")
    try:
        import sys
        sys.path.insert(0, str(Path.home() / "mekong-cli"))
        from src.raas.autopilot_executor import execute_all_tenants
        tenant_result = execute_all_tenants()
        print(f"  Tenants: {tenant_result['tenants']}, Missions: {tenant_result['missions']}")
    except Exception as e:
        print(f"  [TENANT_ERROR] {e}")

    print(f"\n{'=' * 60}")
    print(f"  Cycle #{cycle} complete: {completed_this_cycle}/{len(MISSIONS)} own + tenant missions")
    print(f"  Total lifetime: {state['total_missions']} missions")
    print(f"  Next cycle in {CYCLE_INTERVAL_HOURS}h")
    print(f"{'=' * 60}")

    return state


def acquire_lock():
    """Prevent duplicate daemon processes via file lock."""
    PID_FILE.parent.mkdir(parents=True, exist_ok=True)
    lock_fd = open(str(PID_FILE), "w")
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        lock_fd.write(str(os.getpid()))
        lock_fd.flush()
        return lock_fd
    except IOError:
        print(f"Another daemon already running (lock: {PID_FILE})")
        sys.exit(0)


def main():
    """Main daemon loop — runs forever."""
    import traceback as _tb

    # Single-instance lock
    lock = acquire_lock()

    # Redirect all output to log file for debugging
    log_path = Path.home() / ".mekong" / "daemon-debug.log"
    sys.stdout = open(str(log_path), "a", buffering=1)
    sys.stderr = sys.stdout

    print(f"\n{'='*40} DAEMON START {'='*40}")
    print(f"PID: {os.getpid()}")
    print(f"Gateway: {GATEWAY_URL}")
    print(f"Reports: {REPORTS_DIR}")
    print(f"GITHUB_TOKEN: {'SET' if GITHUB_TOKEN else 'NOT SET'}")
    print(f"Cycle interval: {CYCLE_INTERVAL_HOURS}h")

    state = load_state()

    while True:
        try:
            state = run_cycle(state)
        except Exception as e:
            print(f"[CYCLE_ERROR] {e}")
            _tb.print_exc()
            save_state(state)  # Save whatever we have

        # Sleep until next cycle
        print(f"\nSleeping {CYCLE_INTERVAL_HOURS}h until next cycle...", flush=True)
        time.sleep(CYCLE_INTERVAL_HOURS * 3600)


if __name__ == "__main__":
    main()
