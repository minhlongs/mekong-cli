"""Seed layer configuration — local-first, no cloud required."""

import os
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent

# LLM — Ollama local
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
LLM_MODEL = os.getenv("LLM_MODEL", "qwen2.5-coder:7b")
EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text:latest")

# Memory
CHROMA_PATH = str(BASE_DIR / "data" / "chroma")
SQLITE_PATH = str(BASE_DIR / "data" / "sqlite" / "memory.db")

# Outputs
OUTPUTS_DIR = str(BASE_DIR / "outputs")

# Timeout
LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", "120"))
