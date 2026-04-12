"""OpenClaw Autonomous Daemon — Paperclip Model.

Runs CONTINUOUSLY on M1 Max. Every cycle:
1. Pick next priority mission
2. Execute via gateway API (eat own dogfood)
3. Auto-publish content to GitHub Discussions
4. Sleep 4 hours, repeat

This IS the a16z solo company: agents do everything, human sleeps.
"""
import json
import os
import time
import datetime
import hashlib
import requests
from pathlib import Path

# Config — use gateway API (not direct LLM)
GATEWAY_URL = os.getenv("GATEWAY_URL", "http://localhost:8000")
REPORTS_DIR = Path.home() / "mekong-cli" / "content" / "openclaw-reports"
STATE_FILE = Path.home() / ".mekong" / "daemon-state.json"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GITHUB_REPO = "longtho638-jpg/mekong-cli"
CYCLE_INTERVAL_HOURS = 4

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
    """Execute mission via gateway API (eat own dogfood)."""
    try:
        r = requests.post(f"{GATEWAY_URL}/raas/missions",
            json={"goal": goal},
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=10,
        )
        if r.status_code == 202:
            mission_id = r.json()["id"]
            # Poll for completion (max 2 min)
            for _ in range(12):
                time.sleep(10)
                status_r = requests.get(
                    f"{GATEWAY_URL}/raas/missions/{mission_id}",
                    headers={"Authorization": f"Bearer {api_key}"},
                    timeout=10,
                )
                if status_r.status_code == 200:
                    data = status_r.json()
                    if data["status"] == "completed":
                        return data.get("output", goal)
                    if data["status"] == "failed":
                        return f"[FAILED] {data.get('error_message', 'unknown')}"
            return "[TIMEOUT] Mission did not complete in 2 minutes"
        elif r.status_code == 402:
            return "[NO_CREDITS] Daemon out of credits"
        else:
            return f"[ERROR] HTTP {r.status_code}: {r.text[:200]}"
    except Exception as e:
        return f"[ERROR] {e}"

    # Fallback: direct Ollama call if gateway fails
    try:
        r = requests.post("http://localhost:11434/v1/chat/completions",
            json={
                "model": "qwen2.5-coder:7b",
                "messages": [{"role": "user", "content": goal}],
                "max_tokens": 2000,
            }, timeout=120)
        return r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"[FALLBACK_ERROR] {e}"


def publish_to_github(title: str, body: str, category: str = "General"):
    """Auto-publish content as GitHub Discussion."""
    if not GITHUB_TOKEN:
        print("  [SKIP] No GITHUB_TOKEN — cannot publish")
        return False

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
            return True
    except Exception as e:
        print(f"  [PUBLISH_ERROR] {e}")
    return False


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

        # Auto-publish if flagged
        if mission.get("publish") and not result.startswith("["):
            title = mission["goal"][:100]
            body = result + "\n\n---\n*Auto-generated by [MekongMind OpenClaw Daemon](https://mekongmind.pages.dev)*"
            publish_to_github(title, body, mission.get("category", "General"))

        state["completed"][mhash] = now
        state["total_missions"] = state.get("total_missions", 0) + 1
        completed_this_cycle += 1
        time.sleep(5)  # Cool down

    state["cycle_count"] = cycle
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


def main():
    """Main daemon loop — runs forever."""
    print("OpenClaw Autonomous Daemon starting...")
    print(f"Gateway: {GATEWAY_URL}")
    print(f"Reports: {REPORTS_DIR}")
    print(f"Cycle interval: {CYCLE_INTERVAL_HOURS}h")

    state = load_state()

    while True:
        try:
            state = run_cycle(state)
        except Exception as e:
            print(f"[CYCLE_ERROR] {e}")

        # Sleep until next cycle
        print(f"\nSleeping {CYCLE_INTERVAL_HOURS}h until next cycle...")
        time.sleep(CYCLE_INTERVAL_HOURS * 3600)


if __name__ == "__main__":
    main()
