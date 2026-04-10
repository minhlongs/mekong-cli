# Mekong IDE Demo Script (2 minutes)

## Opening (10s)
"Mekong IDE — one AI operating system, 22 departments, 290 commands."

## Show: Terminal (30s)
```bash
# Start the gateway
uvicorn src.gateway:app --port 8000

# Run a finance mission
curl -X POST http://localhost:8000/v1/missions \
  -H "Content-Type: application/json" \
  -d '{"goal": "Create invoice for client ABC, web development, $5000"}'
```

Narrate: "I type what I want in plain English. The system classifies it — CFO department, finance domain — matches the right command, and executes."

## Show: Output (20s)
Show the structured invoice output. Highlight:
- Classified correctly (CFO)
- Matched command (accounting-invoice-batch)
- Structured output (not generic LLM gibberish)
- 1 credit deducted

## Show: Different departments (30s)
```bash
# Marketing
curl ... -d '{"goal": "Write content calendar for April"}'

# Legal  
curl ... -d '{"goal": "Review NDA for red flags"}'

# Engineering
curl ... -d '{"goal": "Deploy staging with rollback plan"}'
```

Narrate: "Same API, same subscription. Finance, marketing, legal, engineering — 22 departments, all included."

## Show: Departments endpoint (10s)
```bash
curl http://localhost:8000/v1/departments | python3 -m json.tool
```

Narrate: "290 commands, organized by department. Every tier gets everything."

## Pricing slide (10s)
- Starter $49/mo — 200 credits
- Growth $149/mo — 1,000 credits
- Pro $499/mo — 5,000 credits

## Close (10s)
"Mekong IDE. Run your entire business with AI agents. On your own hardware."

URL: agencyos.network
