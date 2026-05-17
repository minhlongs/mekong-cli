"""Mission Control API server — FastAPI wrapper around seed agents."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

try:
    from fastapi import FastAPI, Form
    from fastapi.responses import HTMLResponse, JSONResponse
    from fastapi.staticfiles import StaticFiles
    import uvicorn
except ImportError:
    print("Install: pip install fastapi uvicorn")
    sys.exit(1)

from seed.main import run as seed_run

app = FastAPI(title="Mekong Seed API", version="1.0.0")

WEB_DIR = Path(__file__).parent.parent / "web"


@app.get("/", response_class=HTMLResponse)
async def index():
    html_file = WEB_DIR / "mission-control.html"
    if html_file.exists():
        return HTMLResponse(content=html_file.read_text())
    return HTMLResponse("<h1>Mission Control</h1><p>UI not found</p>")


@app.post("/api/task")
async def run_task(task: str = Form(...)):
    """Run a task through the seed agent pipeline."""
    try:
        result = seed_run(task)
        outputs = result.get("outputs", [])
        test_result = result.get("test_result", {})
        plan = result.get("plan", [])

        lines = [f"📋 Plan: {len(plan)} steps"]
        for i, step in enumerate(plan, 1):
            lines.append(f"  {i}. {step}")
        lines.append("")
        lines.append(f"📁 Outputs ({len(outputs)}):")
        for out in outputs:
            lines.append(f"  → {out}")
        if test_result:
            passed = test_result.get("passed", True)
            score = test_result.get("score", "?")
            lines.append(f"\n{'✅' if passed else '❌'} Test: score={score}/10")
        return "\n".join(lines)
    except Exception as e:
        return f"❌ Error: {e}"


@app.get("/health")
async def health():
    return JSONResponse({"status": "ok", "service": "mekong-seed"})


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8765, reload=False)
