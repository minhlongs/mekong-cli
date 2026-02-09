#!/usr/bin/env python3
"""
🐉 Qwen Bridge Proxy — Python v1.0 (DRAGON Tier)
Port: 8081

Converts Anthropic Messages API → OpenAI Chat Completions API
specifically for Qwen Models.
"""

import os
import json
import time
import uuid
import requests
from flask import Flask, request, Response, jsonify

app = Flask(__name__)

# --- CONFIG ---
PORT = 8081
DASHSCOPE_API_KEY = os.environ.get(
    "DASHSCOPE_API_KEY", "sk-6219c93290f14b32b047342ca8b0bea9"
)  # Default from settings
DASHSCOPE_BASE_URL = (
    "https://dashscope-intl.aliyuncs.com/compatible-mode/v1/chat/completions"
)

MODEL_MAP = {
    "qwen-coder-plus": "qwen2.5-coder-32b-instruct",
    "claude-3-5-sonnet-20241022": "qwen2.5-coder-32b-instruct",
    "claude-sonnet-4-20250514": "qwen2.5-coder-32b-instruct",
}


def anthropic_to_openai(data):
    messages = []
    system_prompt = data.get("system", "")
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})

    for msg in data.get("messages", []):
        role = msg.get("role")
        content = msg.get("content")

        if isinstance(content, list):
            text_parts = [
                part.get("text", "") for part in content if part.get("type") == "text"
            ]
            content = "\n".join(text_parts)

        messages.append({"role": role, "content": content})

    requested_model = data.get("model", "qwen-coder-plus")
    target_model = MODEL_MAP.get(requested_model, "qwen2.5-coder-32b-instruct")

    return {
        "model": target_model,
        "messages": messages,
        "stream": data.get("stream", False),
        "max_tokens": data.get("max_tokens", 4096),
        "temperature": data.get("temperature", 0.7),
    }


def openai_to_anthropic(oa_res, model):
    choice = oa_res["choices"][0]
    usage = oa_res.get("usage", {"prompt_tokens": 0, "completion_tokens": 0})

    return {
        "id": f"msg_{uuid.uuid4().hex}",
        "type": "message",
        "role": "assistant",
        "content": [{"type": "text", "text": choice["message"]["content"]}],
        "model": model,
        "stop_reason": "end_turn"
        if choice["finish_reason"] == "stop"
        else choice["finish_reason"],
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

    headers = {
        "Authorization": f"Bearer {DASHSCOPE_API_KEY}",
        "Content-Type": "application/json",
    }

    res = requests.post(DASHSCOPE_BASE_URL, headers=headers, json=oa_payload)

    if res.status_code != 200:
        return jsonify(
            {"error": "Upstream error", "details": res.text}
        ), res.status_code

    return jsonify(openai_to_anthropic(res.json(), data.get("model")))


@app.route("/health")
def health():
    return jsonify({"status": "ok", "service": "🐉 Qwen Bridge Python", "port": PORT})


if __name__ == "__main__":
    print(f"🐉 Qwen Bridge starting on port {PORT}...")
    app.run(port=PORT, host="0.0.0.0")
