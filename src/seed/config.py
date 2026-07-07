"""Seed config — Ollama + model settings."""
from __future__ import annotations

import os

OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
LLM_MODEL: str = os.getenv("LLM_MODEL", "llama3")
EMBED_MODEL: str = os.getenv("EMBED_MODEL", "llama3")
LLM_TIMEOUT: int = int(os.getenv("LLM_TIMEOUT", "30"))

CHROMA_PATH: str = os.getenv("CHROMA_PATH", "/tmp/seed_chroma")
SQLITE_PATH: str = os.getenv("SQLITE_PATH", "/tmp/seed_memory.db")
OUTPUTS_DIR: str = os.getenv("OUTPUTS_DIR", "/tmp/seed_outputs")
