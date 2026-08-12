import json, urllib.request, sys

KEY = "sk-b9eb30e8d08b6389-bdc6e3-a980fe1f"
BASE = "http://omnimbp.local:20128"

def chat(model, messages, max_tokens=50, timeout=120):
    body = json.dumps({
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
    }).encode()
    req = urllib.request.Request(BASE + "/api/v1/chat/completions", body, {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + KEY,
    })
    try:
        r = urllib.request.urlopen(req, timeout=timeout)
        d = json.loads(r.read().decode())
        return d["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as e:
        return f"HTTP {e.code}: {e.read().decode()[:120]}"
    except Exception as e:
        return f"FAIL: {str(e)[:120]}"

if __name__ == "__main__":
    model = sys.argv[1] if len(sys.argv) > 1 else "claude-fable-5"
    print("MODEL:", model)
    print("REPLY:", chat(model, [{"role": "user", "content": "Reply exactly: PONG"}])[:200])
