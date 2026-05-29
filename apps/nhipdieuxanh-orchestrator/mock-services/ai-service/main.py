import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Nhịp Điệu Xanh AI Microservice")

class AnalyzeRequest(BaseModel):
    text: str

class PersonaRequest(BaseModel):
    intent: str
    budget: float

@app.get("/healthz")
def health_check():
    return {"status": "healthy", "service": "ai-service"}

@app.post("/api/ai/analyze-sentiment")
def analyze_sentiment(req: AnalyzeRequest):
    text_lower = req.text.lower()
    score = 0
    if "mua" in text_lower or "cần" in text_lower:
        score += 0.5
    if "đẹp" in text_lower or "thích" in text_lower:
        score += 0.4
    
    sentiment = "POSITIVE" if score > 0.4 else "NEUTRAL"
    return {"sentiment": sentiment, "score": score}

@app.post("/api/ai/classify-persona")
def classify_persona(req: PersonaRequest):
    intent = req.intent.lower()
    budget = req.budget

    if "học" in intent or "trường" in intent:
        persona = "Phụ huynh học sinh"
    elif "đầu tư" in intent or budget >= 3000000000:
        persona = "Nhà đầu tư"
    else:
        persona = "Người mua nhà định cư"

    return {"persona": persona}
