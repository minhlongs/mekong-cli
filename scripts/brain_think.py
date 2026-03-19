#!/usr/bin/env python3
"""CTO Brain Think — calls Ollama /api/generate and extracts /command.

Qwen3 ALWAYS uses thinking mode: 'response' is empty, output is in 'thinking'.
We search BOTH fields for /command patterns.
Uses /api/generate (NOT /api/chat — chat API returns empty content with qwen3).
"""
import json
import urllib.request
import sys
import re
import os


def main():
    ollama_url = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434")
    ollama_model = os.environ.get("OLLAMA_MODEL", "qwen3:32b")

    stdin_text = sys.stdin.read().strip()
    if not stdin_text:
        print("", end="")
        return

    # Use /api/generate — NOT /api/chat (qwen3 chat API returns empty content)
    prompt_text = (
        "/no_think\n"
        "Reply with ONLY a single slash command. No explanation. Examples:\n"
        '/cook "implement user auth"\n'
        '/debug "fix login error"\n'
        '/review "check code quality"\n'
        "Now reply with ONLY the /command:\n\n"
        + stdin_text
    )

    data = json.dumps({
        "model": ollama_model,
        "prompt": prompt_text,
        "stream": False,
        "keep_alive": "24h",
        "options": {"temperature": 0.3, "num_predict": 150, "num_ctx": 4096},
    }).encode()

    try:
        req = urllib.request.Request(
            f"{ollama_url}/api/generate",
            data=data,
            headers={"Content-Type": "application/json"},
        )
        resp = urllib.request.urlopen(req, timeout=120)
        d = json.loads(resp.read())

        # Qwen3 puts output in 'thinking' field, 'response' is usually empty
        response_text = d.get("response", "").strip()
        thinking_text = d.get("thinking", "").strip()
        all_text = (response_text + "\n" + thinking_text).strip()

        if not all_text:
            print("", end="")
            return

        # Extract /command — priority: quoted args > unquoted > raw text
        m = re.search(r'(/[\w][\w:-]*\s+"[^"]+")', all_text)
        if m:
            print(m.group(1))
            return

        m = re.search(r'(/[\w][\w:-]*(?:\s+[^\n]+)?)', all_text)
        if m:
            cmd = m.group(0).strip()[:200]
            # Filter garbage: must start with valid command prefix
            if cmd.startswith("/") and len(cmd) > 2:
                print(cmd)
                return

        # No command found — output empty (will trigger fallback)
        print("", end="")

    except Exception as e:
        print(f"BRAIN_ERROR: {e}", file=sys.stderr)
        print("", end="")


if __name__ == "__main__":
    main()
