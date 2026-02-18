from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
import asyncio
import os

app = FastAPI()

# Database Simulation (Redis)
proxy_health_scores = {"198.51.100.1": 100, "203.0.113.5": 45} 

class ErrorReport(BaseModel):
    ip: str
    error_code: int

@app.post("/internal/webhook/report-error")
async def report_proxy_failure(report: ErrorReport, bg_tasks: BackgroundTasks):
    """ Golang calls this when WAF blocks an IP """
    bg_tasks.add_task(analyze_and_quarantine, report.ip, report.error_code)
    return {"status": "Agent is investigating"}

async def analyze_and_quarantine(ip: str, error_code: int):
    print(f"🕵️ [SecOps] Report Received: IP {ip} hit {error_code}")
    
    if error_code in [403, 429]: 
        score = proxy_health_scores.get(ip, 100) - 20
        proxy_health_scores[ip] = score
        print(f"⚠️ Trust Score for {ip}: {score}")
        
        if score < 50:
            print(f"🚨 BLACKLISTED {ip}. Initiating IP Rotation Protocol...")
            # Logic: Remove from Redis -> Call Proxy Provider API -> Add New IP
            # In a real scenario, this would trigger a webhook to the Proxy Provider
            print(f"🔄 [Auto-Healing] Ordering replacement for {ip} from BrightData...")
            await asyncio.sleep(1) 
            proxy_health_scores[ip] = 100 # Reset for simulation after healing
            print(f"✅ [Auto-Healing] New IP acquired. Score reset to 100.")

@app.get("/")
def read_root():
    return {
        "status": "Agentic Brain Online", 
        "mode": "Hybrid-Waterfall",
        "scores": proxy_health_scores,
        "active_nodes": len([s for s in proxy_health_scores.values() if s > 50])
    }
