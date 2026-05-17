"""OpenClaw background service — runs inside Gateway process.

Start/stop via API. IDE displays live status.
"""
import datetime
import json
import os
import threading
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

MLX_URL = os.getenv("MLX_URL", "http://localhost:11435/v1/chat/completions")
MLX_MODEL = os.getenv("MLX_MODEL", "mlx-community/Qwen2.5-Coder-32B-Instruct-4bit")
_BASE = Path(os.getenv("MEKONG_HOME", Path(__file__).resolve().parent.parent.parent))
REPORTS_DIR = os.getenv("OPENCLAW_REPORTS_DIR", str(_BASE / "content" / "openclaw-reports"))
COMMANDS_DIR = os.getenv("COMMANDS_DIR", str(_BASE / ".claude" / "commands"))

MISSIONS = [
    {"dept": "marketing", "cmd": "marketing-seo", "goal": "SEO audit for mekongmind.com"},
    {"dept": "marketing", "cmd": "marketing-campaign", "goal": "Launch campaign plan for Product Hunt"},
    {"dept": "content", "cmd": "content-blog", "goal": "Blog: 5 Ways to Automate Dev Operations"},
    {"dept": "content", "cmd": "content-social", "goal": "7-day social media calendar"},
    {"dept": "sales", "cmd": "sales-pipeline", "goal": "ICP and sales pipeline for CTOs"},
    {"dept": "growth", "cmd": "growth-experiment", "goal": "3 growth experiments for user acquisition"},
    {"dept": "finance", "cmd": "finance-budget-plan", "goal": "Monthly budget plan"},
    {"dept": "analyst", "cmd": "analyst-report", "goal": "Competitive analysis vs Cursor/Windsurf"},
    {"dept": "legal", "cmd": "legal-policy", "goal": "Terms of Service draft"},
    {"dept": "ops", "cmd": "ops-status", "goal": "Operations status report"},
    {"dept": "security", "cmd": "security-scan", "goal": "Security audit of mekongmind.com"},
]

@dataclass
class DaemonState:
    running: bool = False
    current_mission: int = -1
    total_missions: int = len(MISSIONS)
    completed: int = 0
    current_dept: str = ""
    current_goal: str = ""
    reports: list = field(default_factory=list)
    started_at: str = ""
    thread: threading.Thread = field(default=None, repr=False)

state = DaemonState()

def call_llm(prompt: str) -> str:
    payload = json.dumps({
        "model": MLX_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 2000,
    }).encode()
    req = urllib.request.Request(
        MLX_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            data = json.loads(resp.read().decode())
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        return f"[ERROR] {e}"

def run_loop():
    os.makedirs(REPORTS_DIR, exist_ok=True)
    state.started_at = datetime.datetime.now().isoformat()
    for i, m in enumerate(MISSIONS):
        if not state.running:
            break
        state.current_mission = i
        state.current_dept = m["dept"]
        state.current_goal = m["goal"]
        ts = datetime.datetime.now().strftime("%Y%m%d-%H%M")
        prompt = f"You are OpenClaw. Dept: {m['dept']}. Command: /{m['cmd']}. Goal: {m['goal']}. Produce structured report. Do NOT use word AI."
        result = call_llm(prompt)
        fname = f"{ts}-{m[dept]}-{m[cmd]}.md"
        path = os.path.join(REPORTS_DIR, fname)
        with open(path, "w") as f:
            f.write(f"# {m[goal]}\n\n{result}")
        state.completed += 1
        state.reports.append({"file": fname, "dept": m["dept"], "size": len(result)})
    state.running = False
    state.current_goal = "idle"

def start():
    if state.running:
        return {"status": "already_running"}
    state.running = True
    state.completed = 0
    state.reports = []
    state.thread = threading.Thread(target=run_loop, daemon=True)
    state.thread.start()
    return {"status": "started", "missions": state.total_missions}

def stop():
    state.running = False
    return {"status": "stopped", "completed": state.completed}

def get_status():
    return {
        "running": state.running,
        "current_mission": state.current_mission + 1,
        "total_missions": state.total_missions,
        "completed": state.completed,
        "current_dept": state.current_dept,
        "current_goal": state.current_goal,
        "started_at": state.started_at,
        "reports_count": len(state.reports),
    }
