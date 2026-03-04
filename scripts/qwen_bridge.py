#!/usr/bin/env python3
"""
🐉 Qwen Bridge Proxy — Python v1.0 (DRAGON Tier)
Port: 8081

Converts Anthropic Messages API → OpenAI Chat Completions API
specifically for Qwen Models. Supports multi-key Load Balancing.
"""

import os
import json
import uuid
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# --- CONFIG ---
PORT = 8081

# Load keys from env first (comma-separated), fallback to hardcoded (may be expired)
_env_keys = [k.strip() for k in os.environ.get("DASHSCOPE_API_KEYS", "").split(",") if k.strip()]
_single_key = os.environ.get("DASHSCOPE_API_KEY", "").strip()
if _single_key and _single_key not in _env_keys:
    _env_keys.append(_single_key)

# Hardcoded keys as fallback — update when rotating keys
_HARDCODED_KEYS = [
    "sk-4d2965a589ca4d9da2ea05e4bd200d97",  # minhlong.rice@gmail.com (2026-02-27)
]

API_KEYS = _env_keys if _env_keys else _HARDCODED_KEYS
if not _env_keys:
    print("⚠️  WARNING: No DASHSCOPE_API_KEYS env var — using expired hardcoded keys!")
    print("⚠️  Set DASHSCOPE_API_KEYS=key1,key2 or DASHSCOPE_API_KEY=key")

DASHSCOPE_BASE_URL = (
    "https://dashscope-intl.aliyuncs.com/compatible-mode/v1/chat/completions"
)

# Rotation index
_current_key_idx = 0

# MODEL MAP (DashScope Compatible Mode names)
# If using dashscope-intl.aliyuncs.com/compatible-mode/v1, use these:
MODEL_MAP = {
    "qwen-coder-plus": "qwen-plus",  # Mapping to qwen-plus as more reliable fallback
    "claude-3-5-sonnet-20241022": "qwen-max",
    "claude-sonnet-4-20250514": "qwen-plus",
}


def get_next_key():
    global _current_key_idx
    key = API_KEYS[_current_key_idx]
    _current_key_idx = (_current_key_idx + 1) % len(API_KEYS)
    return key


def anthropic_to_openai(data):
    messages = []
    system_prompt = data.get("system", "")
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})

    for msg in data.get("messages", []):
        role = msg.get("role")
        content = msg.get("content")

        if isinstance(content, list):
            # Handle mixed content (text + tool_use) or tool_result
            new_content = []
            for part in content:
                if part.get("type") == "text":
                    new_content.append(part.get("text", ""))
                elif part.get("type") == "tool_use":
                    # Convert tool_use to OpenAI tool_calls
                    messages.append(
                        {
                            "role": "assistant",
                            "tool_calls": [
                                {
                                    "id": part.get("id"),
                                    "type": "function",
                                    "function": {
                                        "name": part.get("name"),
                                        "arguments": json.dumps(part.get("input")),
                                    },
                                }
                            ],
                        }
                    )
                    # Skip appending to new_content as we handled it via a separate message
                    # note: this is a simplification; authentic conversion might be more complex
                    # if text and tool_use are mixed in one turn.
                    continue
                elif part.get("type") == "tool_result":
                    # Convert tool_result to OpenAI tool message
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": part.get("tool_use_id"),
                            "content": str(part.get("content", "")),
                        }
                    )
                    continue

            if new_content:
                messages.append({"role": role, "content": "\n".join(new_content)})
            continue  # handled above

        messages.append({"role": role, "content": content})

    requested_model = data.get("model", "qwen-coder-plus")
    target_model = MODEL_MAP.get(requested_model, "qwen2.5-coder-32b-instruct")

    payload = {
        "model": target_model,
        "messages": messages,
        "stream": data.get("stream", False),
        "max_tokens": data.get("max_tokens", 4096),
        "temperature": data.get("temperature", 0.7),
    }

    # Convert Tools
    if "tools" in data:
        openai_tools = []
        for tool in data["tools"]:
            openai_tools.append(
                {
                    "type": "function",
                    "function": {
                        "name": tool["name"],
                        "description": tool.get("description", ""),
                        "parameters": tool.get("input_schema", {}),
                    },
                }
            )
        payload["tools"] = openai_tools

    return payload


def openai_to_anthropic(oa_res, model):
    choice = oa_res["choices"][0]
    message_content = []

    # 1. Handle Text Content
    if choice["message"].get("content"):
        message_content.append({"type": "text", "text": choice["message"]["content"]})

    # 2. Handle Tool Calls
    if choice["message"].get("tool_calls"):
        for tc in choice["message"]["tool_calls"]:
            message_content.append(
                {
                    "type": "tool_use",
                    "id": tc["id"],
                    "name": tc["function"]["name"],
                    "input": json.loads(tc["function"]["arguments"]),
                }
            )

    # 3. Handle Finish Reason
    stop_reason = choice["finish_reason"]
    if stop_reason == "stop":
        stop_reason = "end_turn"
    elif stop_reason == "tool_calls":
        stop_reason = "tool_use"
    elif stop_reason == "length":
        stop_reason = "max_tokens"

    usage = oa_res.get("usage", {"prompt_tokens": 0, "completion_tokens": 0})

    return {
        "id": f"msg_{uuid.uuid4().hex}",
        "type": "message",
        "role": "assistant",
        "content": message_content,
        "model": model,
        "stop_reason": stop_reason,
        "usage": {
            "input_tokens": usage["prompt_tokens"],
            "output_tokens": usage["completion_tokens"],
        },
    }


@app.route("/v1/messages", methods=["POST"])
def messages():
    data = request.json
    stream = data.get("stream", False)

    if stream:
        return jsonify(
            {"error": "Streaming not yet implemented in simplified python bridge"}
        ), 400

    oa_payload = anthropic_to_openai(data)

    # Try multiple keys if needed
    last_error = None
    for _ in range(len(API_KEYS)):
        current_key = get_next_key()
        headers = {
            "Authorization": f"Bearer {current_key}",
            "Content-Type": "application/json",
        }

        print(f"🐉 Using key: ...{current_key[-4:]}")
        try:
            res = requests.post(
                DASHSCOPE_BASE_URL, headers=headers, json=oa_payload, timeout=60
            )
            if res.status_code == 200:
                return jsonify(openai_to_anthropic(res.json(), data.get("model")))

            last_error = res.text
            print(
                f"❌ Key ...{current_key[-4:]} failed: {res.status_code} - {res.text}"
            )

            if res.status_code not in [429, 401, 403, 404]:
                break  # Non-retryable error

        except Exception as e:
            last_error = str(e)
            print(f"❌ Key ...{current_key[-4:]} error: {e}")

    return jsonify({"error": "All keys failed", "details": last_error}), 502


@app.route("/health")
def health():
    return jsonify({"status": "ok", "service": "🐉 Qwen Bridge Python", "port": PORT})


if __name__ == "__main__":
    print(f"🐉 Qwen Bridge starting on port {PORT}...")
    app.run(port=PORT, host="0.0.0.0")
