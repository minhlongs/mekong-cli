#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path("/Users/macbook/mekong-cli")
LOCAL_RUNTIME = PROJECT_ROOT / "mekong" / "local_llm" / "runtime.py"


class LocalPort:
    key = "local_m1_max"
    title = "Local LLM on MacBook M1 Max"
    description = "Local runtime without remote API"
    kind = "local_model"
    suggested_model = "local-llm"


def is_available() -> bool:
    try:
        spec = importlib.util.find_spec("llama_cpp")
        return spec is not None
    except Exception:
        return False


def prepare() -> dict[str, Any]:
    runtime_path = LOCAL_RUNTIME
    if not runtime_path.exists():
        raise FileNotFoundError(f"Missing local runtime at {runtime_path}")

    spec = importlib.util.spec_from_file_location("mekong_local_runtime", runtime_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    engine = module.Engine(runtime_path.parent)
    engine.load()

    return {
        "provider": "local",
        "port": LocalPort().key,
        "model": LocalPort().suggested_model,
        "runtime_path": str(runtime_path),
        "engine": engine,
    }


if __name__ == "__main__":
    print("Local LLM port ready:", is_available())
