"""
Mekong CLI - Gateway Server (OpenClaw Hybrid Commander)

FastAPI server exposing the Plan-Execute-Verify engine via HTTP.
Includes "Washing Machine" dashboard for one-button operation.
Enables remote command execution: Cloud Ra Lenh + Local Thuc Thi.
"""

import json
import os
from dataclasses import asdict
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from src.core.llm_client import get_client
from src.core.orchestrator import RecipeOrchestrator


# -- Preset recipes: "Washing Machine" one-button actions --

PRESET_ACTIONS = [
    {"id": "deploy", "icon": "\U0001f680", "label": "Quick Deploy",
     "goal": "deploy all applications to production",
     "label_vi": "Tri\u1ec3n Khai Nhanh"},
    {"id": "leads", "icon": "\U0001f50d", "label": "Audit Leads",
     "goal": "scan and audit all lead generation sources",
     "label_vi": "Ki\u1ec3m Tra Leads"},
    {"id": "content", "icon": "\U0001f4dd", "label": "Plan Content",
     "goal": "create a content plan for this week",
     "label_vi": "L\u00ean K\u1ebf Ho\u1ea1ch N\u1ed9i Dung"},
    {"id": "ask", "icon": "\U0001f4a1", "label": "Ask AI",
     "goal": "answer my question using AI analysis",
     "label_vi": "H\u1ecfi AI"},
    {"id": "review", "icon": "\U0001f9d0", "label": "Code Review",
     "goal": "review recent code changes for quality and security",
     "label_vi": "Ki\u1ec3m Tra Code"},
    {"id": "status", "icon": "\U0001f4ca", "label": "System Status",
     "goal": "check system health and report status of all services",
     "label_vi": "Tr\u1ea1ng Th\u00e1i H\u1ec7 Th\u1ed1ng"},
]


# -- Request / Response models --

class CommandRequest(BaseModel):
    """Incoming command from the cloud brain"""
    goal: str = Field(..., min_length=1, description="High-level goal to execute")
    token: str = Field(..., min_length=1, description="API authentication token")


class StepSummary(BaseModel):
    """Summary of a single execution step"""
    order: int
    title: str
    passed: bool
    exit_code: int
    summary: str


class HumanSummary(BaseModel):
    """Non-dev friendly summary in both languages"""
    en: str
    vi: str


class CommandResponse(BaseModel):
    """Response returned to the cloud caller"""
    status: str
    goal: str
    total_steps: int
    completed_steps: int
    failed_steps: int
    success_rate: float
    errors: List[str]
    warnings: List[str]
    steps: List[StepSummary]
    trace: Optional[Dict[str, Any]] = None
    human_summary: Optional[HumanSummary] = None


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = "ok"
    version: str = "0.3.0"
    engine: str = "Plan-Execute-Verify"


class PresetAction(BaseModel):
    """A preset one-button action for the dashboard"""
    id: str
    icon: str
    label: str
    label_vi: str
    goal: str


# -- Token verification --

def verify_token(token: str) -> None:
    """Verify the provided token against MEKONG_API_TOKEN env var."""
    expected = os.environ.get("MEKONG_API_TOKEN")
    if not expected:
        raise HTTPException(
            status_code=500,
            detail="MEKONG_API_TOKEN not configured on server",
        )
    if token != expected:
        raise HTTPException(status_code=401, detail="Invalid token")


def build_human_summary(result) -> HumanSummary:
    """Generate a non-dev friendly summary from orchestration result."""
    status = result.status.value
    rate = result.success_rate

    if status == "success":
        en = f"All done! {result.completed_steps} tasks completed successfully."
        vi = f"Xong! {result.completed_steps} tac vu hoan thanh thanh cong."
    elif status == "partial":
        en = (f"Partially done. {result.completed_steps}/{result.total_steps} "
              f"tasks completed ({rate:.0f}%). Some issues need attention.")
        vi = (f"Hoan thanh mot phan. {result.completed_steps}/{result.total_steps} "
              f"tac vu ({rate:.0f}%). Can xem lai mot so van de.")
    else:
        en = f"Failed. {result.failed_steps} tasks had problems. Please check errors."
        vi = f"That bai. {result.failed_steps} tac vu gap loi. Vui long kiem tra."

    return HumanSummary(en=en, vi=vi)


# -- Dashboard HTML: The Washing Machine UI --
# Uses safe DOM methods (createElement, textContent) instead of innerHTML

DASHBOARD_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Mekong Dashboard</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
background:#0f172a;color:#e2e8f0;min-height:100vh;display:flex;flex-direction:column}
header{text-align:center;padding:2rem 1rem 1rem;border-bottom:1px solid #1e293b}
header h1{font-size:1.8rem;background:linear-gradient(135deg,#38bdf8,#818cf8);
-webkit-background-clip:text;-webkit-text-fill-color:transparent}
header p{color:#94a3b8;margin-top:.3rem;font-size:.9rem}
.token-bar{display:flex;gap:.5rem;max-width:400px;margin:1rem auto 0;align-items:center}
.token-bar input{flex:1;padding:.5rem .75rem;border:1px solid #334155;border-radius:.5rem;
background:#1e293b;color:#e2e8f0;font-size:.85rem}
.token-bar button{padding:.5rem 1rem;border:none;border-radius:.5rem;
background:#334155;color:#e2e8f0;cursor:pointer;font-size:.85rem}
.token-bar button:hover{background:#475569}
main{flex:1;padding:1.5rem;max-width:800px;margin:0 auto;width:100%}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:1rem;margin-top:1rem}
.btn{display:flex;flex-direction:column;align-items:center;justify-content:center;
padding:1.5rem 1rem;border:2px solid #334155;border-radius:1rem;background:#1e293b;
cursor:pointer;transition:all .2s;min-height:140px;text-align:center}
.btn:hover{border-color:#38bdf8;transform:translateY(-2px);box-shadow:0 4px 20px rgba(56,189,248,.15)}
.btn:active{transform:translateY(0)}
.btn.running{border-color:#f59e0b;animation:pulse 1.5s infinite}
.btn.success{border-color:#22c55e}
.btn.error{border-color:#ef4444}
.btn .icon{font-size:2.5rem;margin-bottom:.5rem}
.btn .label{font-size:1rem;font-weight:600}
.btn .label-vi{font-size:.75rem;color:#94a3b8;margin-top:.2rem}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.7}}
#result{margin-top:1.5rem;padding:1rem;border-radius:.75rem;background:#1e293b;
border:1px solid #334155;display:none;max-height:400px;overflow-y:auto}
#result.show{display:block}
.custom-bar{display:flex;gap:.5rem;margin-top:1rem}
.custom-bar input{flex:1;padding:.75rem 1rem;border:1px solid #334155;border-radius:.75rem;
background:#1e293b;color:#e2e8f0;font-size:1rem}
.custom-bar button{padding:.75rem 1.5rem;border:none;border-radius:.75rem;
background:linear-gradient(135deg,#38bdf8,#818cf8);color:#0f172a;
font-weight:700;cursor:pointer;font-size:1rem}
.custom-bar button:hover{opacity:.9}
footer{text-align:center;padding:1rem;color:#475569;font-size:.75rem;border-top:1px solid #1e293b}
.summary-box{padding:.75rem;border-radius:.5rem;margin-bottom:.75rem}
.summary-ok{background:#052e16;border:1px solid #22c55e}
.summary-fail{background:#450a0a;border:1px solid #ef4444}
.summary-partial{background:#422006;border:1px solid #f59e0b}
details{margin-top:.5rem}
details summary{cursor:pointer;color:#94a3b8;font-size:.85rem}
details pre{font-size:.75rem;color:#94a3b8;white-space:pre-wrap;margin-top:.5rem}
</style>
</head>
<body>
<header>
<h1>Mekong Dashboard</h1>
<p>AgencyOS — Press a button, get things done.</p>
<div class="token-bar">
<input type="password" id="token" placeholder="API Token" />
<button onclick="saveToken()">Save</button>
</div>
</header>
<main>
<div class="grid" id="buttons"></div>
<div class="custom-bar">
<input type="text" id="custom-goal" placeholder="Or type a custom goal..." />
<button onclick="runCustom()">Run</button>
</div>
<div id="result"></div>
</main>
<footer>Mekong CLI v0.3.0 — OpenClaw Hybrid Commander</footer>
<script>
var PRESETS=__PRESETS_JSON__;
function saveToken(){localStorage.setItem('mekong_token',document.getElementById('token').value)}
function getToken(){return document.getElementById('token').value||localStorage.getItem('mekong_token')||''}
function el(tag,cls,text){var e=document.createElement(tag);if(cls)e.className=cls;if(text)e.textContent=text;return e}
window.onload=function(){
document.getElementById('token').value=localStorage.getItem('mekong_token')||'';
var grid=document.getElementById('buttons');
PRESETS.forEach(function(p){
var d=el('div','btn');d.id='btn-'+p.id;
d.appendChild(el('span','icon',p.icon));
d.appendChild(el('span','label',p.label));
d.appendChild(el('span','label-vi',p.label_vi));
d.onclick=function(){runGoal(p.goal,p.id)};
grid.appendChild(d);
});
};
function showResult(content){var r=document.getElementById('result');r.className='show';while(r.firstChild)r.removeChild(r.firstChild);if(typeof content==='string'){r.appendChild(el('h3','',content))}else{r.appendChild(content)}}
async function runGoal(goal,btnId){
var token=getToken();if(!token){alert('Please enter your API token first.');return}
var btn=btnId?document.getElementById('btn-'+btnId):null;
if(btn)btn.className='btn running';
showResult('Running...');
try{
var r=await fetch('/cmd',{method:'POST',headers:{'Content-Type':'application/json'},
body:JSON.stringify({goal:goal,token:token})});
var d=await r.json();
if(!r.ok){var errBox=el('div','');errBox.appendChild(el('h3','','Error'));errBox.appendChild(el('pre','',JSON.stringify(d,null,2)));showResult(errBox);if(btn)btn.className='btn error';return}
var frag=document.createDocumentFragment();
var hs=d.human_summary;var cls=d.status==='success'?'summary-ok':d.status==='partial'?'summary-partial':'summary-fail';
var box=el('div','summary-box '+cls);
if(hs){box.appendChild(el('strong','',hs.en));var viLine=el('div','',hs.vi);viLine.style.marginTop='.3rem';viLine.style.color='#94a3b8';box.appendChild(viLine)}
else{box.appendChild(el('div','','Status: '+d.status+' ('+d.success_rate+'%)'))}
frag.appendChild(box);
var details=document.createElement('details');details.appendChild(el('summary','','Technical Details'));details.appendChild(el('pre','',JSON.stringify(d,null,2)));
frag.appendChild(details);showResult(frag);
if(btn)btn.className='btn '+(d.status==='success'?'success':'error');
}catch(e){showResult('Network Error: '+e.message);if(btn)btn.className='btn error'}
}
function runCustom(){var g=document.getElementById('custom-goal').value.trim();
if(!g){alert('Please enter a goal.');return}runGoal(g,null)}
</script>
</body>
</html>"""


# -- FastAPI app factory --

def create_app() -> FastAPI:
    """Create and configure the gateway FastAPI application."""
    gateway = FastAPI(
        title="Mekong Gateway",
        description="OpenClaw Hybrid Commander — Cloud Ra Lenh, Local Thuc Thi",
        version="0.3.0",
    )

    @gateway.get("/", response_class=HTMLResponse)
    def dashboard():
        """Serve the Washing Machine dashboard UI"""
        presets_json = json.dumps(PRESET_ACTIONS)
        html = DASHBOARD_HTML.replace("__PRESETS_JSON__", presets_json)
        return HTMLResponse(content=html)

    @gateway.get("/presets", response_model=List[PresetAction])
    def list_presets():
        """List available one-button preset actions"""
        return [PresetAction(**p) for p in PRESET_ACTIONS]

    @gateway.get("/health", response_model=HealthResponse)
    def health_check():
        """Health check endpoint"""
        return HealthResponse()

    @gateway.post("/cmd", response_model=CommandResponse)
    def execute_command(req: CommandRequest):
        """
        Execute a goal through the Plan-Execute-Verify engine.

        Requires valid MEKONG_API_TOKEN for authentication.
        Returns orchestration result with optional execution trace.
        """
        verify_token(req.token)

        try:
            llm_client = get_client()
            orchestrator = RecipeOrchestrator(
                llm_client=llm_client if llm_client.is_available else None,
                strict_verification=True,
                enable_rollback=True,
            )

            result = orchestrator.run_from_goal(req.goal)

            # Build step summaries
            steps = [
                StepSummary(
                    order=sr.step.order,
                    title=sr.step.title,
                    passed=sr.verification.passed,
                    exit_code=sr.execution.exit_code,
                    summary=sr.verification.summary,
                )
                for sr in result.step_results
            ]

            # Read execution trace if available
            trace = None
            trace_obj = orchestrator.telemetry.get_trace()
            if trace_obj:
                trace = asdict(trace_obj)

            # Build human-friendly summary
            human_summary = build_human_summary(result)

            return CommandResponse(
                status=result.status.value,
                goal=req.goal,
                total_steps=result.total_steps,
                completed_steps=result.completed_steps,
                failed_steps=result.failed_steps,
                success_rate=result.success_rate,
                errors=result.errors,
                warnings=result.warnings,
                steps=steps,
                trace=trace,
                human_summary=human_summary,
            )

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    return gateway


# Module-level app instance for uvicorn
app = create_app()


__all__ = [
    "create_app",
    "app",
    "CommandRequest",
    "CommandResponse",
    "HealthResponse",
    "HumanSummary",
    "StepSummary",
    "PresetAction",
    "PRESET_ACTIONS",
    "DASHBOARD_HTML",
    "verify_token",
    "build_human_summary",
]
