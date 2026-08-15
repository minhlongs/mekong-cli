import os
import sys
import json
import urllib.request
import asyncio
from fastapi import FastAPI
from pydantic import BaseModel
from aiokafka import AIOKafkaConsumer
import asyncpg

# Add current directory to path to ensure retriever can be imported
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from retriever import AskPythonRetriever

app = FastAPI(title="Nhịp Điệu Xanh AI Microservice")

class AnalyzeRequest(BaseModel):
    text: str

class PersonaRequest(BaseModel):
    intent: str
    budget: float

class QueryAgentRequest(BaseModel):
    question: str
    limit: int = 5
    options: dict = None

def format_prompt(question: str, chunks: list[dict]) -> str:
    xml_chunks = []
    for chunk in chunks:
        xml_chunks.append(f"""  <chunk id="{chunk.get('id', '')}">
    <title>{chunk.get('title', '')}</title>
    <file_path>{chunk.get('filePath', '')}</file_path>
    <content>{chunk.get('content', '')}</content>
  </chunk>""")
    
    chunks_str = "\n".join(xml_chunks)
    
    prompt = f"""You are a helpful AI assistant for the Nhịp Điệu Xanh application.
Use the following context contained in XML tags to answer the user's question. If you don't know the answer or if the context doesn't contain information to answer, say so.

<context>
{chunks_str}
</context>

<question>
{question}
</question>

Please provide a clear and helpful response."""
    return prompt

def call_completions(prompt: str) -> str:
    # 1. Try local OpenAI endpoint
    url = "http://localhost:11437/v1/chat/completions"
    headers = {
        "Content-Type": "application/json"
    }
    payload = {
        "model": "qwen2.5-coder",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2
    }
    
    try:
        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=5.0) as response:
            res = json.loads(response.read().decode("utf-8"))
            if "choices" in res and len(res["choices"]) > 0:
                content = res["choices"][0]["message"].get("content")
                if content:
                    return content
    except Exception as e:
        print(f"Local completions call failed: {e}")
        
    # 2. Try remote OpenAI API if key exists
    api_key = os.environ.get("OPENAI_API_KEY")
    if api_key:
        try:
            url = "https://api.openai.com/v1/chat/completions"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
            req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=10.0) as response:
                res = json.loads(response.read().decode("utf-8"))
                if "choices" in res and len(res["choices"]) > 0:
                    content = res["choices"][0]["message"].get("content")
                    if content:
                        return content
        except Exception as e:
            print(f"Remote OpenAI completions call failed: {e}")
            
    return None

def generate_heuristic_response(question: str, chunks: list[dict]) -> str:
    if not chunks:
        return "Tôi không tìm thấy thông tin nào liên quan đến câu hỏi của bạn trong cơ sở dữ liệu Nhịp Điệu Xanh."
    
    response_lines = [
        f"Dựa trên dữ liệu Nhịp Điệu Xanh, tôi tìm thấy một số thông tin liên quan đến câu hỏi '{question}':\n"
    ]
    for i, c in enumerate(chunks[:3]):
        title = c.get('title', 'Tài liệu')
        content = c.get('content', '')
        snippet = content[:150] + "..." if len(content) > 150 else content
        response_lines.append(f"{i+1}. **{title}**: {snippet}")
        
    response_lines.append("\n(Lưu ý: Đây là câu trả lời được mô phỏng trực tiếp từ ngữ cảnh tìm kiếm do hệ thống LLM cục bộ hiện tại không phản hồi)")
    return "\n".join(response_lines)

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

@app.post("/api/ai/query-agent")
def query_agent(req: QueryAgentRequest):
    retriever = None
    try:
        retriever = AskPythonRetriever()
        # Retrieve relevant chunks using the new retriever
        chunks = retriever.retrieve(req.question, limit=req.limit)
        
        # Format them into an XML structured prompt
        prompt = format_prompt(req.question, chunks)
        
        # Call completions (local or remote)
        response_text = call_completions(prompt)
        
        model_used = "llm"
        if not response_text:
            # Fall back to heuristic summary from context
            response_text = generate_heuristic_response(req.question, chunks)
            model_used = "heuristic-fallback"
            
        return {
            "success": True,
            "response": response_text,
            "chunks": chunks,
            "model": model_used
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "response": f"Đã xảy ra lỗi khi xử lý truy vấn: {str(e)}",
            "chunks": []
        }
    finally:
        if retriever:
            retriever.close()

async def process_lead_event(event: dict):
    data = event.get("data", {})
    lead_id = data.get("id")
    need = data.get("need", "")
    budget_str = data.get("budget", "0")
    
    if not lead_id:
        return
        
    print(f"[Kafka Consumer] Analyzing lead {lead_id}...")
    
    # 1. Analyze sentiment (heuristic)
    text_lower = need.lower()
    score = 0
    if "mua" in text_lower or "cần" in text_lower:
        score += 0.5
    if "đẹp" in text_lower or "thích" in text_lower:
        score += 0.4
    sentiment = "POSITIVE" if score > 0.4 else "NEUTRAL"
    
    # 2. Classify buyer persona (heuristic)
    budget = 0.0
    try:
        import re
        nums = re.findall(r'\d+(?:\.\d+)?', budget_str)
        if nums:
            budget = float(nums[0]) * 1e9
    except Exception:
        pass
        
    if "học" in text_lower or "trường" in text_lower:
        persona = "Phụ huynh học sinh"
    elif "đầu tư" in text_lower or budget >= 3e9:
        persona = "Nhà đầu tư"
    else:
        persona = "Người mua nhà định cư"
        
    # 3. Update PostgreSQL
    db_url = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/nhipdieuxanh_db")
    
    is_docker = os.path.exists('/.dockerenv')
    if not is_docker and "postgres:5432" in db_url:
        db_url = db_url.replace("postgres:5432", "localhost:5432")
        
    try:
        conn = await asyncpg.connect(db_url)
        try:
            await conn.execute(
                "UPDATE leads SET sentiment = $1, persona = $2 WHERE id = $3",
                sentiment, persona, lead_id
            )
            print(f"[Kafka Consumer] Successfully updated Lead {lead_id} with sentiment={sentiment}, persona={persona}")
        finally:
            await conn.close()
    except Exception as db_err:
        print(f"[Kafka Consumer] Database update failed for lead {lead_id}: {db_err}")

async def run_kafka_consumer():
    kafka_servers = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    
    is_docker = os.path.exists('/.dockerenv')
    if not is_docker:
        kafka_servers = "localhost:9094"
            
    print(f"[Kafka Consumer] Waiting for Kafka to be ready at {kafka_servers}...")
    await asyncio.sleep(5)
    
    print(f"[Kafka Consumer] Connecting to {kafka_servers}...")
    consumer = AIOKafkaConsumer(
        'nhipdieuxanh-leads',
        bootstrap_servers=kafka_servers,
        group_id="nhipdieuxanh-ai-group",
        auto_offset_reset='earliest'
    )
    
    connected = False
    for attempt in range(10):
        try:
            await consumer.start()
            connected = True
            print("[Kafka Consumer] Connected successfully to Kafka topic 'nhipdieuxanh-leads'!")
            break
        except Exception as e:
            print(f"[Kafka Consumer] Connection attempt {attempt+1} failed: {e}")
            await asyncio.sleep(3)
            
    if not connected:
        print("[Kafka Consumer] Failed to connect to Kafka. Exiting consumer.")
        return
        
    try:
        async for msg in consumer:
            try:
                event = json.loads(msg.value.decode('utf-8'))
                print(f"[Kafka Consumer] Received event: {event}")
                await process_lead_event(event)
            except Exception as e:
                print(f"[Kafka Consumer] Error processing message: {e}")
    except Exception as run_err:
        print(f"[Kafka Consumer] Run error: {run_err}")
    finally:
        await consumer.stop()

@app.on_event("startup")
async def startup_event():
    # Start the consumer task in the background
    asyncio.create_task(run_kafka_consumer())
