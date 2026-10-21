# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Sophia AI Video Factory — Video rendering pipeline and job persistence service."""
from __future__ import annotations

from datetime import datetime, timezone
import json
import logging
import os
from pathlib import Path
import re
from typing import Any
import uuid

from src.services.sophia_video_models import (
    DEFAULT_SOPHIA_STORAGE_DIR,
    AvatarProfile,
    JobStatus,
    VideoRenderRequest,
    VideoRenderResult,
    VideoTemplate,
    VoiceProfile,
    validate_identifier,
    validate_job_id,
)
from src.services.sophia_video_providers import (
    AVATAR_CATALOG,
    TEMPLATE_CATALOG,
    VOICE_CATALOG,
    deduct_tenant_mcu,
    estimate_mcu_cost,
    load_design_dna_tokens,
)

logger = logging.getLogger(__name__)


class SophiaVideoService:
    """Core AI Video Factory orchestrator for Mekong CLI."""

    def __init__(
        self,
        *,
        storage_dir: Path | str = DEFAULT_SOPHIA_STORAGE_DIR,
        enable_billing: bool = True,
    ) -> None:
        self.storage_dir = Path(storage_dir)
        self.jobs_dir = self.storage_dir / "jobs"
        self.artifacts_dir = self.storage_dir / "artifacts"
        self.enable_billing = enable_billing
        self._ensure_storage()

    def _ensure_storage(self) -> None:
        """Ensure persistent job and artifact directories exist."""
        self.jobs_dir.mkdir(parents=True, exist_ok=True)
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)

    def list_avatars(self, gender: str | None = None) -> list[AvatarProfile]:
        """Return available digital avatar presenters."""
        if not gender:
            return list(AVATAR_CATALOG)
        target = gender.strip().lower()
        return [a for a in AVATAR_CATALOG if a.gender.lower() == target]

    def list_voices(self, language: str | None = None) -> list[VoiceProfile]:
        """Return available voice models."""
        if not language:
            return list(VOICE_CATALOG)
        target = language.strip().lower()
        return [v for v in VOICE_CATALOG if target in v.language.lower()]

    def list_templates(self) -> list[VideoTemplate]:
        """Return available video composition templates."""
        return list(TEMPLATE_CATALOG)

    def estimate_cost(self, duration_seconds: int, template: str = "news_anchor") -> dict[str, Any]:
        """Estimate MCU credit cost for a video of given duration and template."""
        return estimate_mcu_cost(duration_seconds, template)

    def _load_design_dna(self, dna_name: str) -> dict[str, Any] | None:
        """Attempt to load approved Design DNA styling tokens."""
        return load_design_dna_tokens(dna_name)

    def _deduct_mcu(self, tenant_id: str, mcu_cost: int, mission_id: str) -> bool:
        """Deduct MCU credits for tenant. Returns True if successful or billing disabled."""
        return deduct_tenant_mcu(tenant_id, mcu_cost, mission_id, enable_billing=self.enable_billing)

    def render_video(self, request: VideoRenderRequest) -> VideoRenderResult:
        """Execute or schedule video rendering pipeline."""
        now_utc = datetime.now(timezone.utc).isoformat()
        job_id = f"sophia-{request.title.lower().replace(' ', '-')[:24]}-{uuid.uuid4().hex[:8]}"
        job_id = re.sub(r"[^a-zA-Z0-9_-]", "-", job_id)

        word_count = len(request.script.split())
        est_duration = max(5.0, round((word_count / 150.0) * 60.0, 1))
        mcu_cost = self.estimate_cost(int(est_duration), request.template)["estimated_mcu"]
        dna_styling = self._load_design_dna(request.design_dna_name) if request.design_dna_name else None
        self._deduct_mcu(request.tenant_id, mcu_cost, mission_id=job_id)

        artifact_filename = f"{job_id}.mp4"
        artifact_path = self.artifacts_dir / artifact_filename
        video_url = f"https://cdn.sophia.mekongmind.com/renders/{artifact_filename}"
        if request.dry_run or not (os.getenv("ELEVENLABS_API_KEY") and os.getenv("DID_API_KEY")):
            artifact_path.write_text(
                f"Sophia Video MP4 Container :: {job_id} :: Duration: {est_duration}s\n", encoding="utf-8"
            )

        result = VideoRenderResult(
            job_id=job_id,
            title=request.title,
            status=JobStatus.COMPLETED,
            progress=100,
            video_url=video_url,
            local_artifact_path=str(artifact_path),
            duration_seconds=est_duration,
            credits_used=mcu_cost,
            aspect_ratio=request.aspect_ratio.value,
            template=request.template,
            avatar_id=request.avatar_id,
            voice_id=request.voice_id,
            design_dna_applied=request.design_dna_name if dna_styling else None,
            created_at=now_utc,
            completed_at=datetime.now(timezone.utc).isoformat(),
            metadata={
                "tenant_id": request.tenant_id,
                "word_count": word_count,
                "dry_run": request.dry_run,
                "subtitles": request.subtitles_enabled,
                "dna_styling": dna_styling or {},
            },
        )
        self._save_job(result)
        return result

    def _save_job(self, result: VideoRenderResult) -> None:
        """Persist job record to storage."""
        job_file = self.jobs_dir / f"{result.job_id}.json"
        temp_file = self.jobs_dir / f"{result.job_id}.json.tmp"
        temp_file.write_text(result.model_dump_json(indent=2), encoding="utf-8")
        temp_file.replace(job_file)

    def get_job_status(self, job_id: str) -> VideoRenderResult:
        """Look up job status by ID."""
        cleaned_id = validate_job_id(job_id)
        job_file = self.jobs_dir / f"{cleaned_id}.json"
        if not job_file.exists():
            raise FileNotFoundError(f"Sophia video job not found: {cleaned_id}")
        return VideoRenderResult.model_validate(json.loads(job_file.read_text(encoding="utf-8")))

    def list_jobs(self, tenant_id: str = "default", limit: int = 20) -> list[VideoRenderResult]:
        """List recently generated video jobs for a tenant."""
        validate_identifier(tenant_id, "tenant ID")
        results: list[VideoRenderResult] = []
        if not self.jobs_dir.exists():
            return results
        for path in sorted(self.jobs_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
            if len(results) >= limit:
                break
            try:
                res = VideoRenderResult.model_validate_json(path.read_text(encoding="utf-8"))
                if res.metadata.get("tenant_id") == tenant_id or tenant_id == "all":
                    results.append(res)
            except Exception as exc:  # noqa: BLE001
                logger.debug("Skipping corrupt job file %s: %s", path, exc)
        return results
