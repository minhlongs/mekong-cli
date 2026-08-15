#!/usr/bin/env python3
"""CTO Brain Think — calls Ollama /api/generate and extracts /command.

Strategy: Try think:false first (clean response), fallback to thinking parse.
Qwen3 in thinking mode puts output in 'thinking' field, 'response' is empty.
"""
import json
import urllib.request
import sys
import re
import os
import time

CMD_NAMES = (
    # Core commands
    "cook|fix|debug|review|test|plan(?:(?:\s+|:)hard|(?:\s+|:)fast)?|code|ask|scout|"
    "backend-api-build|frontend-ui-build|check-and-commit|deploy|ship|brainstorm|"
    # Engineering layer (from cto-command-catalog.json)
    "engineering-refactor|eng-sprint-execute|eng-tech-debt|"
    "dev-feature|dev-bug-sprint|dev-pr-review|"
    "backend-db-task|tech-architecture-review|tech-migration|"
    # Ops layer
    "ops-health-sweep|ops-security-audit|"
    "devops-deploy-pipeline|devops-rollback|"
    "sre-incident|sre-morning-check|release-ship|release-hotfix|"
    # Product layer
    "product-discovery|product-launch-feature|product-sprint-plan|"
    "product-retrospective|product-competitive-intel|"
    # Business layer
    "business-campaign-launch|business-client-onboard|"
    "business-revenue-engine|business-quarterly-review"
)


def call_ollama(url, model, prompt, think=True, timeout=30, retries=3):
    """Call Ollama generate API with retry + backoff, return parsed JSON."""
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "keep_alive": "5m",
        "options": {"temperature": 0.3, "num_predict": 100, "num_ctx": 4096},
    }
    if not think:
        payload["think"] = False
        payload["options"]["num_predict"] = 50
    data = json.dumps(payload).encode()
    last_err = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(
                f"{url}/api/generate", data=data,
                headers={"Content-Type": "application/json"},
            )
            resp = urllib.request.urlopen(req, timeout=timeout)
            return json.loads(resp.read())
        except Exception as e:
            last_err = e
            if attempt < retries - 1:
                wait = 2 ** attempt
                print(f"BRAIN_RETRY: attempt {attempt+1}/{retries} failed ({e}), waiting {wait}s", file=sys.stderr)
                time.sleep(wait)
    raise last_err


def extract_cmd(text):
    """Extract /command from text. Returns normalized command or empty string."""
    if not text:
        return ""
    # Priority 1: /command "quoted args"
    m = re.search(rf'(/{CMD_NAMES}\s+"[^"]+")', text, re.IGNORECASE)
    if m:
        return normalize(m.group(1))
    # Priority 2: /command at start of line (clean output)
    m = re.search(rf'^(/{CMD_NAMES}(?:\s+"[^"]+")?)$', text, re.MULTILINE | re.IGNORECASE)
    if m:
        return normalize(m.group(1))
    return ""


def extract_from_thinking(text):
    """Parse thinking text for the model's final command recommendation."""
    if not text:
        return ""
    # Find ALL /command "quoted" — take LAST (conclusion)
    matches = re.findall(rf'/{CMD_NAMES}\s+"[^"]+"', text, re.IGNORECASE)
    if matches:
        return normalize(matches[-1])
    # Look for conclusion patterns: "So: /fix ...", "I'll use /cook ..."
    m = re.search(
        rf'(?:so|therefore|thus|final|answer|output|assign|use)[:\s]+'
        rf'(/{CMD_NAMES}(?:\s+"[^"]+")?)',
        text, re.IGNORECASE,
    )
    if m:
        return normalize(m.group(1))
    # Last resort: last standalone /command mention (not in reasoning context)
    matches = re.findall(rf'(?:^|\n)\s*(/{CMD_NAMES})\s', text, re.IGNORECASE)
    if matches:
        return normalize(matches[-1])
    return ""


def normalize(cmd):
    """Lowercase command name, ensure / prefix, strip trailing punctuation."""
    if not cmd:
        return ""
    cmd = cmd.strip()
    # Ensure / prefix
    if not cmd.startswith("/"):
        cmd = "/" + cmd
    parts = cmd.split(" ", 1)
    parts[0] = parts[0].lower()
    return " ".join(parts).rstrip(".,;:!?").strip()


def call_external_brain(api_url, api_key, model_name, prompt, timeout=30):
    """Call external chat completions API with native urllib.request."""
    payload = {
        "model": model_name,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,
        "max_tokens": 100
    }
    data = json.dumps(payload).encode('utf-8')
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    target_url = api_url
    if not target_url.endswith("/chat/completions"):
        target_url = f"{target_url.rstrip('/')}/chat/completions"
    req = urllib.request.Request(
        target_url,
        data=data,
        headers=headers,
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        res_data = json.loads(resp.read().decode('utf-8'))
        return res_data["choices"][0]["message"]["content"]


def main():
    url = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434")
    model = os.environ.get("OLLAMA_MODEL", "qwen3:32b")

    stdin_text = sys.stdin.read().strip()
    if not stdin_text:
        return

    prompt = (
        "You are CTO Brain. Reply with ONLY a single slash command.\n"
        "Valid: /cook, /fix, /debug, /review, /test, /plan hard, /scout, "
        "/backend-api-build, /frontend-ui-build, /check-and-commit\n"
        'Format: /command "specific task" (NEVER use colon — /plan hard NOT /plan:hard)\n\n'
        + stdin_text
    )

    api_url = os.environ.get("BRAIN_API_URL")
    api_key = os.environ.get("BRAIN_API_KEY")
    brain_model = os.environ.get("BRAIN_MODEL") or model

    if api_url and api_key:
        try:
            content = call_external_brain(api_url, api_key, brain_model, prompt)
            cmd = extract_cmd(content)
            if not cmd:
                cmd = extract_from_thinking(content)
            if not cmd and content:
                # Check for any slash command in the response as a fallback
                m = re.search(rf'(/{CMD_NAMES}(?:\s+"[^"]+")?)', content, re.IGNORECASE)
                if m:
                    cmd = normalize(m.group(1))
            if cmd:
                print(cmd)
                return
        except Exception as e:
            print(f"BRAIN_EXTERNAL_ERROR: {e}. Falling back to Ollama.", file=sys.stderr)

    try:
        # Strategy 1: think:false (clean response, may be slow/timeout)
        try:
            d = call_ollama(url, model, prompt, think=False, timeout=10)
            cmd = extract_cmd(d.get("response", ""))
            if cmd:
                print(cmd)
                return
        except Exception:
            pass  # Timeout expected — fall through to thinking mode

        # Strategy 2: thinking mode (fast, parse from thinking field)
        d = call_ollama(url, model, prompt, think=True, timeout=30)
        # Check response first
        cmd = extract_cmd(d.get("response", ""))
        if cmd:
            print(cmd)
            return
        # Parse thinking
        cmd = extract_from_thinking(d.get("thinking", ""))
        if cmd:
            print(cmd)
            return

    except Exception as e:
        print(f"BRAIN_ERROR: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
