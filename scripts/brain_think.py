#!/usr/bin/env python3
"""CTO Brain Think — calls Ollama /api/generate and extracts /command.

Qwen3 ALWAYS uses thinking mode: 'response' is empty, output is in 'thinking'.
We parse thinking text for the LAST /command mentioned (the model's conclusion).
Uses /api/generate (NOT /api/chat — chat API returns empty content with qwen3).
"""
import json
import urllib.request
import sys
import re
import os

# Known valid command prefixes (subset — catches most)
VALID_CMDS = {
    "cook", "fix", "debug", "review", "test", "plan", "code", "ask",
    "plan:hard", "plan:fast", "backend-api-build", "frontend-ui-build",
    "check-and-commit", "scout", "brainstorm", "deploy", "ship",
}


def main():
    ollama_url = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434")
    ollama_model = os.environ.get("OLLAMA_MODEL", "qwen3:32b")

    stdin_text = sys.stdin.read().strip()
    if not stdin_text:
        print("", end="")
        return

    # Prompt: ask for JUST the command, no examples to avoid regex matching them
    prompt_text = (
        "/no_think\n"
        "You are CTO Brain. Given the worker context below, decide the SINGLE "
        "most impactful slash command to assign.\n"
        "Valid commands: /cook, /fix, /debug, /review, /test, /plan:hard, "
        "/backend-api-build, /frontend-ui-build, /check-and-commit, /scout\n"
        "Reply format: /command \"specific task description\"\n"
        "Reply with ONLY the command line. No explanation.\n\n"
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

        response_text = d.get("response", "").strip()
        thinking_text = d.get("thinking", "").strip()

        # Check response first (if model actually responds)
        if response_text:
            cmd = extract_command(response_text)
            if cmd:
                print(cmd)
                return

        # Parse thinking for the LAST /command (model's final conclusion)
        if thinking_text:
            cmd = extract_command_from_thinking(thinking_text)
            if cmd:
                print(cmd)
                return

        print("", end="")

    except Exception as e:
        print(f"BRAIN_ERROR: {e}", file=sys.stderr)
        print("", end="")


def extract_command(text: str) -> str:
    """Extract /command from direct response text."""
    m = re.search(r'(/(?:cook|fix|debug|review|test|plan(?::hard|:fast)?|code|ask|scout|backend-api-build|frontend-ui-build|check-and-commit|deploy|ship|brainstorm)\s+"[^"]+")', text)
    if m:
        return m.group(1)
    m = re.search(r'(/(?:cook|fix|debug|review|test|plan(?::hard|:fast)?|code|ask|scout|backend-api-build|frontend-ui-build|check-and-commit|deploy|ship|brainstorm)(?:\s+[^\n]+)?)', text)
    if m:
        return m.group(0).strip()[:250]
    return ""


def extract_command_from_thinking(text: str) -> str:
    """Extract the LAST /command from thinking text (model's conclusion).

    Qwen3 thinks through the problem then concludes with the command.
    We want the LAST match, not the first (which might be from examples).
    """
    # Find ALL /command "args" patterns
    matches = re.findall(
        r'/(?:cook|fix|debug|review|test|plan(?::hard|:fast)?|code|ask|scout|'
        r'backend-api-build|frontend-ui-build|check-and-commit|deploy|ship|brainstorm)'
        r'\s+"[^"]+"',
        text,
    )
    if matches:
        return matches[-1]  # Last match = conclusion

    # Fallback: /command without quotes
    matches = re.findall(
        r'/(?:cook|fix|debug|review|test|plan(?::hard|:fast)?|code|ask|scout|'
        r'backend-api-build|frontend-ui-build|check-and-commit|deploy|ship|brainstorm)'
        r'(?:\s+[^\n]+)?',
        text,
    )
    if matches:
        return matches[-1].strip()[:250]

    return ""


if __name__ == "__main__":
    main()
