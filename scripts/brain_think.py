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


CMD_PATTERN = (
    r"(?:cook|fix|debug|review|test|plan(?::hard|:fast)?|code|ask|scout|"
    r"backend-api-build|frontend-ui-build|check-and-commit|deploy|ship|brainstorm)"
)


def extract_command(text: str) -> str:
    """Extract /command from direct response text."""
    m = re.search(rf"(/{CMD_PATTERN}\s+\"[^\"]+\")", text, re.IGNORECASE)
    if m:
        return normalize_cmd(m.group(1))
    m = re.search(rf"(/{CMD_PATTERN}(?:\s+[^\n]+)?)", text, re.IGNORECASE)
    if m:
        return normalize_cmd(m.group(0).strip()[:250])
    return ""


def extract_command_from_thinking(text: str) -> str:
    """Extract the LAST /command from thinking text (model's conclusion).

    Qwen3 thinks through the problem then concludes with the command.
    We want the LAST match, not the first (which might be from examples).
    Also handles case-insensitive (/Cook → /cook).
    """
    # Find ALL /command "args" patterns (case-insensitive)
    matches = re.findall(rf"/{CMD_PATTERN}\s+\"[^\"]+\"", text, re.IGNORECASE)
    if matches:
        return normalize_cmd(matches[-1])

    # Fallback: /command without quotes
    matches = re.findall(rf"/{CMD_PATTERN}(?:\s+[^\n]+)?", text, re.IGNORECASE)
    if matches:
        return normalize_cmd(matches[-1].strip()[:250])

    # Last resort: look for "I would use /command" or "the command is /command" patterns
    m = re.search(
        rf"(?:use|assign|run|execute|recommend|suggest)\s+(/{CMD_PATTERN})",
        text,
        re.IGNORECASE,
    )
    if m:
        # Build a reasonable command with context
        cmd_name = normalize_cmd(m.group(1))
        # Try to find a description nearby
        desc_match = re.search(r'"([^"]{5,})"', text[m.start():m.start()+200])
        if desc_match:
            return f'{cmd_name} "{desc_match.group(1)}"'
        return cmd_name

    return ""


def normalize_cmd(cmd: str) -> str:
    """Normalize command: /Cook → /cook, strip trailing punctuation."""
    if not cmd:
        return ""
    # Lowercase the command name part (before space or quote)
    parts = cmd.split(" ", 1)
    parts[0] = parts[0].lower()
    result = " ".join(parts).rstrip(".,;:!?")
    return result


if __name__ == "__main__":
    main()
