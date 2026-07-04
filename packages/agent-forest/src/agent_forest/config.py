"""Forest runtime settings loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    return int(raw) if raw else default


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class ForestSettings:
    redis_url: str = "redis://localhost:6379"
    jwt_secret_key: str = ""
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7  # 1 week
    users_yaml: str | None = None
    outputs_dir: Path = field(default_factory=lambda: Path("./outputs").resolve())
    gateway_host: str = "0.0.0.0"  # noqa: S104 — bind in Docker acceptable
    gateway_port: int = 8000
    rate_limit_per_minute: int = 60
    webhook_timeout_seconds: float = 5.0
    worker_poll_seconds: int = 5
    testing: bool = False
    # Docker executor settings (opt-in via FOREST_WORKER_EXECUTOR=docker)
    worker_executor: str = "subprocess"
    docker_image: str = "agent-core:latest"
    docker_timeout_seconds: int = 300
    # Self-heal feedback loop: 1 = single-pass CEO→Dev (back-compat),
    # >=2 enables agent-core FeedbackLoop with Tester+Reviewer+Ops+Analyst + bounded retry.
    feedback_rounds: int = 1
    # Giai đoạn 3.1.A/B: if set, UserStore is backed by SQLite (register_user
    # works). Unset = legacy in-memory YAML defaults.
    db_path: Path | None = None

    @classmethod
    def from_env(cls) -> ForestSettings:
        testing = _env_bool("FOREST_TESTING", False)
        secret = os.getenv("JWT_SECRET_KEY", "")
        if not secret and not testing:
            raise RuntimeError(
                "JWT_SECRET_KEY is required (set FOREST_TESTING=1 to bypass for tests)."
            )
        outputs = Path(os.getenv("FOREST_OUTPUTS", "./outputs")).resolve()
        outputs.mkdir(parents=True, exist_ok=True)
        worker_executor = os.getenv("FOREST_WORKER_EXECUTOR", "subprocess")
        if worker_executor not in {"subprocess", "docker"}:
            raise ValueError(
                f"FOREST_WORKER_EXECUTOR must be 'subprocess' or 'docker', got {worker_executor!r}"
            )
        return cls(
            redis_url=os.getenv("REDIS_URL", "redis://localhost:6379"),
            jwt_secret_key=secret or "test-only-secret-key",
            jwt_algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
            jwt_expire_minutes=_env_int("JWT_EXPIRE_MINUTES", 60 * 24 * 7),
            users_yaml=os.getenv("FOREST_USERS_YAML"),
            outputs_dir=outputs,
            gateway_host=os.getenv("FOREST_HOST", "0.0.0.0"),  # noqa: S104
            gateway_port=_env_int("FOREST_PORT", 8000),
            rate_limit_per_minute=_env_int("FOREST_RATE_LIMIT_PER_MINUTE", 60),
            webhook_timeout_seconds=float(os.getenv("FOREST_WEBHOOK_TIMEOUT", "5")),
            worker_poll_seconds=_env_int("FOREST_WORKER_POLL_SECONDS", 5),
            testing=testing,
            worker_executor=worker_executor,
            docker_image=os.getenv("FOREST_DOCKER_IMAGE", "agent-core:latest"),
            docker_timeout_seconds=_env_int("FOREST_DOCKER_TIMEOUT_SECONDS", 300),
            feedback_rounds=max(1, _env_int("FOREST_FEEDBACK_ROUNDS", 1)),
            db_path=(Path(raw_db).resolve() if (raw_db := os.getenv("FOREST_DB_PATH")) else None),
        )
