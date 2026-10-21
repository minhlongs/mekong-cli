# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
Agent Loop Config & Tool Specs — TIER_CONFIG, TIER_URLS, and OpenAI function definitions.
"""

from __future__ import annotations

import os
from typing import Any

# Dual-model MLX local only (no cloud API)
# Nemotron A3B ~45 tok/s | DeepSeek R1 32B ~10 tok/s
TIER_CONFIG: dict[str, dict[str, Any]] = {
    "fast": {
        "url": os.getenv("NEMOTRON_URL", "http://192.168.11.111:11436/v1"),
        "model": "mlx-community/NVIDIA-Nemotron-3-Nano-30B-A3B-4bit",
        "max_tokens": 256,
        "timeout": 30,
    },
    "deep": {
        "url": os.getenv("DEEPSEEK_R1_URL", "http://192.168.11.111:11435/v1"),
        "model": "mlx-community/DeepSeek-R1-Distill-Qwen-32B-4bit",
        "max_tokens": 512,
        "timeout": 180,
    },
}

TIER_URLS = {k: v["url"] for k, v in TIER_CONFIG.items()}

TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a file from .mekong/ sandbox directory",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative path inside .mekong/"}
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write content to a file in .mekong/ sandbox directory",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative path inside .mekong/"},
                    "content": {"type": "string", "description": "File content"},
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "http_get",
            "description": "Make HTTP GET request to a URL and return response body",
            "parameters": {
                "type": "object",
                "properties": {"url": {"type": "string", "description": "URL to fetch"}},
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_dir",
            "description": "List files in a .mekong/ subdirectory",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative dir path inside .mekong/"}
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "append_log",
            "description": "Append a line to a log file in .mekong/logs/",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {"type": "string", "description": "Log filename"},
                    "message": {"type": "string", "description": "Log message"},
                },
                "required": ["filename", "message"],
            },
        },
    },
]
