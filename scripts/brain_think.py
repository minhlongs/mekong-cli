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

CMD_NAMES = (
    # Core commands
    "cook|fix|debug|review|test|plan(?::hard|:fast)?|code|ask|scout|"
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


def call_ollama(url, model, prompt, think=True, timeout=30):
    """Call Ollama generate API, return parsed JSON."""
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
    req = urllib.request.Request(
        f"{url}/api/generate", data=data,
        headers={"Content-Type": "application/json"},
    )
    resp = urllib.request.urlopen(req, timeout=timeout)
    return json.loads(resp.read())


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


def main():
    url = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434")
    model = os.environ.get("OLLAMA_MODEL", "qwen3:32b")

    stdin_text = sys.stdin.read().strip()
    if not stdin_text:
        return

    prompt = (
        "You are CTO Brain. Reply with ONLY a single slash command.\n"
        "Valid: /cook, /fix, /debug, /review, /test, /plan:hard, /scout, "
        "/backend-api-build, /frontend-ui-build, /check-and-commit\n"
        'Format: /command "specific task"\n\n'
        + stdin_text
    )

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
