#!/usr/bin/env python3
"""CTO Brain Think — calls Ollama and extracts /command from response+thinking."""
import json
import urllib.request
import sys
import re
import os

def main():
    ollama_url = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434")
    ollama_model = os.environ.get("OLLAMA_MODEL", "qwen3:32b")
    
    prompt_text = "/no_think\nDo NOT use thinking. Reply with ONLY the slash command, nothing else.\n" + sys.stdin.read().strip()
    
    data = json.dumps({
        "model": ollama_model,
        "prompt": prompt_text,
        "stream": False,
        "keep_alive": "24h",
        "options": {"temperature": 0.3, "num_predict": 1500}
    }).encode()
    
    try:
        req = urllib.request.Request(
            f"{ollama_url}/api/generate",
            data=data,
            headers={"Content-Type": "application/json"}
        )
        resp = urllib.request.urlopen(req, timeout=60)
        d = json.loads(resp.read())
        
        # qwen3 ALWAYS uses thinking mode — command may be in 'response' OR 'thinking'
        response_text = d.get("response", "").strip()
        thinking_text = d.get("thinking", "").strip()
        
        # Combine both and search for /command patterns
        all_text = response_text + "\n" + thinking_text
        if not all_text.strip():
            for key in ("content", "message", "text"):
                val = d.get(key, "")
                if isinstance(val, dict):
                    val = val.get("content", "")
                all_text += "\n" + str(val).strip()
        
        # Extract /command patterns — accept any slash command (135-command catalog)
        # Priority 1: /command-name "quoted args"
        m = re.search(r'(/[\w][\w:-]*\s+"[^"]+")', all_text)
        if m:
            print(m.group(1))
        else:
            # Priority 2: /command-name unquoted args  
            m = re.search(r'(/[\w][\w:-]*(?:\s+[^\n]+)?)', all_text)
            if m:
                print(m.group(0).strip()[:200])
            else:
                print(all_text[:200] if all_text.strip() else "")
    except Exception:
        print("", end="")

if __name__ == "__main__":
    main()
